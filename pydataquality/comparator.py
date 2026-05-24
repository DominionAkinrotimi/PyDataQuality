import pandas as pd
import numpy as np
from typing import Dict, List, Any
import math
from .analyzer import DataQualityAnalyzer


class DataQualityComparator:
    """
    Compare two DataQualityAnalyzer results to detect data drift and distribution shifts.
    """

    def __init__(
        self,
        reference_analyzer: DataQualityAnalyzer,
        current_analyzer: DataQualityAnalyzer,
    ):
        self.ref = reference_analyzer
        self.curr = current_analyzer

    def compare_statistics(self) -> pd.DataFrame:
        """
        Compare basic statistics between reference and current datasets.
        """
        comparison_data = []

        # Get common columns
        ref_cols = set(self.ref.column_stats.keys())
        curr_cols = set(self.curr.column_stats.keys())
        common_cols = ref_cols.intersection(curr_cols)

        for col in common_cols:
            ref_stats = self.ref.column_stats[col].stats
            curr_stats = self.curr.column_stats[col].stats

            if "mean" in ref_stats and "mean" in curr_stats:
                comparison_data.append(
                    {
                        "column": col,
                        "ref_mean": ref_stats["mean"],
                        "curr_mean": curr_stats["mean"],
                        "pct_change": (
                            (
                                (curr_stats["mean"] - ref_stats["mean"])
                                / ref_stats["mean"]
                            )
                            * 100
                            if ref_stats["mean"] != 0
                            else 0
                        ),
                    }
                )

        return pd.DataFrame(comparison_data)

    def calculate_psi(self, col: str) -> float:
        """
        Calculate the Population Stability Index (PSI) for a column between reference and current datasets.

        PSI Interpretation:
        - PSI < 0.1: Stable / No significant distribution change
        - 0.1 <= PSI < 0.25: Moderate shift / moderate change
        - PSI >= 0.25: Significant shift / major change
        """
        if col not in self.ref.df.columns or col not in self.curr.df.columns:
            return 0.0

        ref_series = self.ref.df[col].dropna()
        curr_series = self.curr.df[col].dropna()

        if len(ref_series) == 0 or len(curr_series) == 0:
            return 0.0

        # Check if numeric
        if pd.api.types.is_numeric_dtype(ref_series):
            try:
                # Decile-based binning using percentiles of reference dataset
                percentiles = np.linspace(0, 100, 11)
                bins = np.percentile(ref_series, percentiles)
                bins = np.unique(bins)

                # Handle edge case where column is highly uniform (e.g., all one value)
                if len(bins) < 2:
                    bins = np.array([bins[0] - 1, bins[0] + 1])

                ref_counts, _ = np.histogram(ref_series, bins=bins)
                curr_counts, _ = np.histogram(curr_series, bins=bins)
            except Exception:
                # Fallback to simple min-max binning
                min_val = min(ref_series.min(), curr_series.min())
                max_val = max(ref_series.max(), curr_series.max())
                if min_val == max_val:
                    bins = np.array([min_val - 1, min_val + 1])
                else:
                    bins = np.linspace(min_val, max_val, 11)
                ref_counts, _ = np.histogram(ref_series, bins=bins)
                curr_counts, _ = np.histogram(curr_series, bins=bins)
        else:
            # Categorical or Boolean column: bin by unique categories
            ref_vc = ref_series.value_counts()
            curr_vc = curr_series.value_counts()

            all_categories = set(ref_vc.index).union(set(curr_vc.index))
            ref_counts = np.array([ref_vc.get(cat, 0) for cat in all_categories])
            curr_counts = np.array([curr_vc.get(cat, 0) for cat in all_categories])

        # Convert absolute counts to percentages
        ref_pct = ref_counts / len(ref_series)
        curr_pct = curr_counts / len(curr_series)

        # Add epsilon to prevent division by zero or log of zero
        eps = 1e-4
        ref_pct = np.where(ref_pct == 0, eps, ref_pct)
        curr_pct = np.where(curr_pct == 0, eps, curr_pct)

        # PSI Formula: Sum((Actual - Expected) * ln(Actual / Expected))
        psi_val = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
        return float(psi_val)

    def calculate_ks(self, col: str) -> Dict[str, float]:
        """
        Calculate Kolmogorov-Smirnov (KS) 2-Sample Test statistic and p-value for numerical columns.
        Attempts to use scipy.stats.ks_2samp if available; otherwise falls back to a pure-numpy calculation.
        """
        if col not in self.ref.df.columns or col not in self.curr.df.columns:
            return {"statistic": 0.0, "p_value": 1.0}

        ref_series = self.ref.df[col].dropna()
        curr_series = self.curr.df[col].dropna()

        if (
            len(ref_series) == 0
            or len(curr_series) == 0
            or not pd.api.types.is_numeric_dtype(ref_series)
        ):
            return {"statistic": 0.0, "p_value": 1.0}

        try:
            # Attempt to use robust SciPy package
            from scipy.stats import ks_2samp

            res = ks_2samp(ref_series, curr_series)
            return {"statistic": float(res.statistic), "p_value": float(res.pvalue)}
        except ImportError:
            # Pure numpy implementation of KS statistic and asymptotic p-value
            data1 = np.sort(ref_series)
            data2 = np.sort(curr_series)
            n1 = len(data1)
            n2 = len(data2)

            data_all = np.concatenate([data1, data2])
            cdf1 = np.searchsorted(data1, data_all, side="right") / n1
            cdf2 = np.searchsorted(data2, data_all, side="right") / n2

            # KS Statistic is the maximum vertical distance between empirical CDFs
            d = np.max(np.abs(cdf1 - cdf2))

            # Asymptotic p-value approximation for 2-sample KS test
            # lambda = d * sqrt((n1 * n2) / (n1 + n2))
            # p-val = 2 * exp(-2 * lambda^2)
            val = d * math.sqrt((n1 * n2) / (n1 + n2))
            p_val = min(1.0, 2.0 * math.exp(-2.0 * val * val))

            return {"statistic": float(d), "p_value": float(p_val)}

    def compare_distributions(self) -> pd.DataFrame:
        """
        Compare distribution drift for all common columns using PSI and KS-test.

        Returns:
            pd.DataFrame: Contains columns, data types, PSI, KS stat, KS p-value, drift status, and mean change %.
        """
        drift_data = []

        ref_cols = set(self.ref.column_stats.keys())
        curr_cols = set(self.curr.column_stats.keys())
        common_cols = ref_cols.intersection(curr_cols)

        for col in common_cols:
            dtype_cat = self.ref._categorize_dtype(self.ref.column_stats[col].dtype)
            ref_stats = self.ref.column_stats[col].stats
            curr_stats = self.curr.column_stats[col].stats

            psi = self.calculate_psi(col)

            # Determine drift status from PSI thresholds
            if psi >= 0.25:
                drift_status = "significant"
            elif psi >= 0.1:
                drift_status = "moderate"
            else:
                drift_status = "stable"

            entry = {
                "column": col,
                "dtype": self.ref.column_stats[col].dtype,
                "psi": psi,
                "drift_status": drift_status,
                "pct_change": np.nan,
                "ks_statistic": np.nan,
                "ks_p_value": np.nan,
            }

            # Include basic mean change if continuous numeric
            if "mean" in ref_stats and "mean" in curr_stats:
                entry["pct_change"] = (
                    ((curr_stats["mean"] - ref_stats["mean"]) / ref_stats["mean"]) * 100
                    if ref_stats["mean"] != 0
                    else 0
                )

            # Perform continuous KS test
            if pd.api.types.is_numeric_dtype(self.ref.df[col]):
                ks_res = self.calculate_ks(col)
                entry["ks_statistic"] = ks_res["statistic"]
                entry["ks_p_value"] = ks_res["p_value"]

            drift_data.append(entry)

        return pd.DataFrame(drift_data)


def compare_reports(analyzer_a, analyzer_b):
    """
    Convenience function to compare two analyzers and return basic mean changes.
    """
    comparator = DataQualityComparator(analyzer_a, analyzer_b)
    return comparator.compare_statistics()


def compare_drift(analyzer_a, analyzer_b) -> pd.DataFrame:
    """
    Convenience function to compare two analyzers for complete statistical drift.
    """
    comparator = DataQualityComparator(analyzer_a, analyzer_b)
    return comparator.compare_distributions()
