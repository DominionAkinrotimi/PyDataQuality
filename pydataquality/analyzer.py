import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import warnings
from dataclasses import dataclass, field
from collections import defaultdict

from .config import QUALITY_THRESHOLDS, REPORT_CONFIG


@dataclass
class QualityIssue:
    """Data class representing a quality issue."""
    column: str
    issue_type: str
    severity: str  # 'critical', 'warning', 'info'
    message: str
    affected_count: int = 0
    affected_percentage: float = 0.0
    details: Dict = field(default_factory=dict)


@dataclass
class ColumnStats:
    """Data class for column statistics."""
    name: str
    dtype: str
    total_count: int
    missing_count: int = 0
    missing_percentage: float = 0.0
    unique_count: int = 0
    stats: Dict = field(default_factory=dict)


class DataQualityAnalyzer:
    """
    Main analyzer class for comprehensive data quality assessment.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe to analyze
    name : str, optional
        Dataset name for reporting
    """
    
    def __init__(self, df: pd.DataFrame, name: str = "Dataset", rules: Dict = None):
        self.df = df.copy()
        self.name = name
        self.rules = rules or {}  # Custom validation rules per column
        self.issues: List[QualityIssue] = []
        self.column_stats: Dict[str, ColumnStats] = {}
        self.dataset_stats: Dict = {}
        
        # Initialize analysis
        self._analyze_dataset_structure()
        self._analyze_columns()
    
    def _analyze_dataset_structure(self):
        """Analyze basic dataset structure."""
        self.dataset_stats = {
            'name': self.name,
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'total_cells': len(self.df) * len(self.df.columns),
            'memory_usage_mb': self.df.memory_usage(deep=True).sum() / 1024**2,
            'analysis_timestamp': datetime.now().isoformat(),
        }
    
    def _analyze_columns(self):
        """Analyze each column in the dataset."""
        for column in self.df.columns:
            self._analyze_single_column(column)
    
    def _analyze_single_column(self, column: str):
        """Analyze a single column."""
        col_data = self.df[column]
        
        # Basic statistics
        missing_count = col_data.isnull().sum()
        total_count = len(col_data)
        missing_percentage = (missing_count / total_count) * 100 if total_count > 0 else 0
        
        # Initialize column stats
        stats = ColumnStats(
            name=column,
            dtype=str(col_data.dtype),
            total_count=total_count,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=col_data.nunique()
        )
        
        # Type-specific analysis
        if pd.api.types.is_numeric_dtype(col_data):
            self._analyze_numeric_column(col_data, stats)
        elif pd.api.types.is_string_dtype(col_data) or pd.api.types.is_categorical_dtype(col_data):
            self._analyze_categorical_column(col_data, stats)
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            self._analyze_datetime_column(col_data, stats)
        
        self.column_stats[column] = stats
    
    def _analyze_numeric_column(self, col_data: pd.Series, stats: ColumnStats):
        """Analyze numeric column statistics."""
        numeric_data = col_data.dropna()
        
        if len(numeric_data) == 0:
            return
        
        # Initialize stats dictionary
        stats_dict = {
            'mean': float(numeric_data.mean()),
            'std': float(numeric_data.std()),
            'min': float(numeric_data.min()),
            'max': float(numeric_data.max()),
            'median': float(numeric_data.median()),
            'skew': float(numeric_data.skew()),
            'kurtosis': float(numeric_data.kurtosis()),
            'zero_count': int((numeric_data == 0).sum()),
            'zero_percentage': float((numeric_data == 0).sum() / len(numeric_data) * 100),
        }
        
        # Only calculate quantiles if not boolean (quantiles don't work on booleans)
        if not pd.api.types.is_bool_dtype(numeric_data):
            try:
                stats_dict['q1'] = float(numeric_data.quantile(0.25))
                stats_dict['q3'] = float(numeric_data.quantile(0.75))
            except Exception:
                # If quantile calculation fails, skip these stats
                pass
        
        stats.stats.update(stats_dict)
        
        # Check for issues
        self._check_numeric_issues(col_data, stats)
    
    def _analyze_categorical_column(self, col_data: pd.Series, stats: ColumnStats):
        """Analyze categorical column statistics."""
        categorical_data = col_data.dropna()
        
        if len(categorical_data) == 0:
            return
        
        stats.stats.update({
            'value_counts': categorical_data.value_counts().to_dict(),
            'most_common': categorical_data.mode().iloc[0] if not categorical_data.mode().empty else None,
            'most_common_count': int(categorical_data.value_counts().iloc[0]) if len(categorical_data) > 0 else 0,
            'most_common_percentage': float(categorical_data.value_counts().iloc[0] / len(categorical_data) * 100) if len(categorical_data) > 0 else 0,
            'entropy': self._calculate_entropy(categorical_data),
        })
        
        # Check for issues
        self._check_categorical_issues(col_data, stats)
    
    def _analyze_datetime_column(self, col_data: pd.Series, stats: ColumnStats):
        """Analyze datetime column statistics."""
        datetime_data = pd.to_datetime(col_data.dropna(), errors='coerce')
        datetime_data = datetime_data[datetime_data.notna()]
        
        if len(datetime_data) == 0:
            return
        
        stats.stats.update({
            'min_date': datetime_data.min().isoformat(),
            'max_date': datetime_data.max().isoformat(),
            'date_range_days': (datetime_data.max() - datetime_data.min()).days,
            'future_dates': int((datetime_data > pd.Timestamp.now()).sum()),
        })
        
        # Check for issues
        self._check_datetime_issues(col_data, stats)
    
    def _check_numeric_issues(self, col_data: pd.Series, stats: ColumnStats):
        """Check for numeric column issues."""
        # Missing values
        if stats.missing_percentage > QUALITY_THRESHOLDS['missing_critical'] * 100:
            self.issues.append(QualityIssue(
                column=stats.name,
                issue_type='missing_values',
                severity='critical',
                message=f'High percentage of missing values ({stats.missing_percentage:.1f}%)',
                affected_count=stats.missing_count,
                affected_percentage=stats.missing_percentage,
                details={'threshold': QUALITY_THRESHOLDS['missing_critical'] * 100}
            ))
        elif stats.missing_percentage > QUALITY_THRESHOLDS['missing_warning'] * 100:
            self.issues.append(QualityIssue(
                column=stats.name,
                issue_type='missing_values',
                severity='warning',
                message=f'Moderate percentage of missing values ({stats.missing_percentage:.1f}%)',
                affected_count=stats.missing_count,
                affected_percentage=stats.missing_percentage,
                details={'threshold': QUALITY_THRESHOLDS['missing_warning'] * 100}
            ))
        
        # Check for outliers if we have enough data and it's not boolean
        numeric_data = col_data.dropna()
        if len(numeric_data) >= 10 and not pd.api.types.is_bool_dtype(numeric_data):
            try:
                Q1 = numeric_data.quantile(0.25)
                Q3 = numeric_data.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - QUALITY_THRESHOLDS['outlier_threshold'] * IQR
                upper_bound = Q3 + QUALITY_THRESHOLDS['outlier_threshold'] * IQR
                
                outliers = numeric_data[(numeric_data < lower_bound) | (numeric_data > upper_bound)]
                
                if len(outliers) > 0:
                    outlier_percentage = (len(outliers) / len(numeric_data)) * 100
                    self.issues.append(QualityIssue(
                        column=stats.name,
                        issue_type='outliers',
                        severity='warning' if outlier_percentage < 10 else 'critical',
                        message=f'Found {len(outliers)} outliers ({outlier_percentage:.1f}% of data)',
                        affected_count=len(outliers),
                        affected_percentage=outlier_percentage,
                        details={
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound),
                            'min_value': float(numeric_data.min()),
                            'max_value': float(numeric_data.max()),
                            'outlier_examples': outliers.head(5).tolist()
                        }
                    ))
            except Exception:
                # If quantile calculation fails, skip outlier detection
                pass
        
        # Check skewness
        if 'skew' in stats.stats and abs(stats.stats['skew']) > QUALITY_THRESHOLDS['skew_threshold']:
            self.issues.append(QualityIssue(
                column=stats.name,
                issue_type='skewed_distribution',
                severity='info',
                message=f'Distribution is skewed (skewness = {stats.stats["skew"]:.2f})',
                affected_count=0,
                affected_percentage=0,
                details={'skewness': stats.stats['skew']}
            ))
    
    def _check_categorical_issues(self, col_data: pd.Series, stats: ColumnStats):
        """Check for categorical column issues."""
        # Missing values check (same as numeric)
        if stats.missing_percentage > QUALITY_THRESHOLDS['missing_critical'] * 100:
            self.issues.append(QualityIssue(
                column=stats.name,
                issue_type='missing_values',
                severity='critical',
                message=f'High percentage of missing values ({stats.missing_percentage:.1f}%)',
                affected_count=stats.missing_count,
                affected_percentage=stats.missing_percentage,
            ))
        elif stats.missing_percentage > QUALITY_THRESHOLDS['missing_warning'] * 100:
            self.issues.append(QualityIssue(
                column=stats.name,
                issue_type='missing_values',
                severity='warning',
                message=f'Moderate percentage of missing values ({stats.missing_percentage:.1f}%)',
                affected_count=stats.missing_count,
                affected_percentage=stats.missing_percentage,
            ))
        
        # Check for low cardinality
        if stats.unique_count / stats.total_count < QUALITY_THRESHOLDS['unique_threshold']:
            self.issues.append(QualityIssue(
                column=stats.name,
                issue_type='low_cardinality',
                severity='info',
                message=f'Low cardinality: {stats.unique_count} unique values for {stats.total_count} rows',
                affected_count=stats.unique_count,
                affected_percentage=(stats.unique_count / stats.total_count) * 100,
            ))
        
        # Check for inconsistent values
        if 'value_counts' in stats.stats:
            value_counts = stats.stats['value_counts']
            # Look for values that might be duplicates with different casing/spacing
            lower_counts = {}
            for value, count in value_counts.items():
                if isinstance(value, str):
                    lower_val = value.strip().lower()
                    if lower_val in lower_counts:
                        lower_counts[lower_val] += count
                    else:
                        lower_counts[lower_val] = count
            
            potential_duplicates = {k: v for k, v in lower_counts.items() if v > 1}
            if len(potential_duplicates) > 0 and len(potential_duplicates) < len(value_counts):
                self.issues.append(QualityIssue(
                    column=stats.name,
                    issue_type='inconsistent_values',
                    severity='warning',
                    message=f'Potential inconsistent values (different casing/spacing)',
                    affected_count=sum(potential_duplicates.values()),
                    affected_percentage=sum(potential_duplicates.values()) / stats.total_count * 100,
                    details={
                        'unique_normalized_values': len(potential_duplicates),
                        'examples': [f"{k} ({v})" for k, v in potential_duplicates.items()][:5]
                    }
                ))
    
    def _check_datetime_issues(self, col_data: pd.Series, stats: ColumnStats):
        """Check for datetime column issues."""
        # Future dates check
        if 'future_dates' in stats.stats and stats.stats['future_dates'] > 0:
            self.issues.append(QualityIssue(
                column=stats.name,
                issue_type='future_dates',
                severity='warning',
                message=f'Found {stats.stats["future_dates"]} future dates',
                affected_count=stats.stats["future_dates"],
                affected_percentage=stats.stats["future_dates"] / stats.total_count * 100,
            ))
    
    def _calculate_entropy(self, series: pd.Series) -> float:
        """Calculate entropy of a categorical series."""
        value_counts = series.value_counts(normalize=True)
        entropy = -np.sum(value_counts * np.log2(value_counts))
        return float(entropy)
    
    def get_summary(self) -> Dict:
        """Get comprehensive analysis summary."""
        summary = {
            'dataset': self.dataset_stats,
            'columns': len(self.column_stats),
            'issues_by_severity': self._count_issues_by_severity(),
            'issues_by_type': self._count_issues_by_type(),
            'column_types': self._count_column_types(),
            'missing_data_overview': self._get_missing_data_overview(),
        }
        return summary
    
    def _count_issues_by_severity(self) -> Dict:
        """Count issues by severity level."""
        counts = {'critical': 0, 'warning': 0, 'info': 0}
        for issue in self.issues:
            counts[issue.severity] += 1
        return counts
    
    def _count_issues_by_type(self) -> Dict:
        """Count issues by type."""
        counts = defaultdict(int)
        for issue in self.issues:
            counts[issue.issue_type] += 1
        return dict(counts)
    
    def _count_column_types(self) -> Dict:
        """Count columns by data type."""
        type_counts = defaultdict(int)
        for stats in self.column_stats.values():
            dtype_category = self._categorize_dtype(stats.dtype)
            type_counts[dtype_category] += 1
        return dict(type_counts)
    
    def _categorize_dtype(self, dtype: str) -> str:
        """Categorize pandas dtype into broader categories."""
        dtype_str = str(dtype)
        if 'int' in dtype_str or 'float' in dtype_str:
            return 'numeric'
        elif 'object' in dtype_str or 'string' in dtype_str or 'category' in dtype_str:
            return 'categorical'
        elif 'datetime' in dtype_str:
            return 'datetime'
        elif 'bool' in dtype_str:
            return 'boolean'
        else:
            return 'other'
    
    def _get_missing_data_overview(self) -> Dict:
        """Get overview of missing data."""
        missing_columns = []
        for col, stats in self.column_stats.items():
            if stats.missing_count > 0:
                missing_columns.append({
                    'column': col,
                    'missing_count': stats.missing_count,
                    'missing_percentage': stats.missing_percentage,
                })
        
        # Sort by missing percentage descending
        missing_columns.sort(key=lambda x: x['missing_percentage'], reverse=True)
        
        return {
            'columns_with_missing': len(missing_columns),
            'total_missing_cells': sum(stats.missing_count for stats in self.column_stats.values()),
            'total_missing_percentage': sum(stats.missing_count for stats in self.column_stats.values()) / 
                                       (self.dataset_stats['rows'] * self.dataset_stats['columns']) * 100
            if self.dataset_stats['rows'] * self.dataset_stats['columns'] > 0 else 0,
            'columns': missing_columns[:REPORT_CONFIG['max_columns_display']],
        }
    
    def get_column_report(self, column: str) -> Optional[Dict]:
        """Get detailed report for a specific column."""
        if column not in self.column_stats:
            return None
        
        stats = self.column_stats[column]
        column_issues = [issue for issue in self.issues if issue.column == column]
        
        report = {
            'name': stats.name,
            'dtype': stats.dtype,
            'total_values': stats.total_count,
            'missing_values': stats.missing_count,
            'missing_percentage': stats.missing_percentage,
            'unique_values': stats.unique_count,
            'issues': [{
                'type': issue.issue_type,
                'severity': issue.severity,
                'message': issue.message,
                'affected_count': issue.affected_count,
                'affected_percentage': issue.affected_percentage,
            } for issue in column_issues],
            'statistics': stats.stats,
        }
        
        return report

    def get_problematic_rows(self, column: str, issue_type: str = 'all') -> pd.DataFrame:
        """
        Get the subset of the dataframe containing problematic rows for a column.
        
        Parameters
        ----------
        column : str
            Column name
        issue_type : str
            Type of issue: 'missing_values', 'outliers', 'all'
            
        Returns
        -------
        pd.DataFrame
            Subset of rows containing the issue
        """
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found in dataframe")
            
        mask = pd.Series(False, index=self.df.index)
        col_data = self.df[column]
        
        # Check missing
        if issue_type in ['missing_values', 'all']:
            mask |= col_data.isnull()
            
        # Check outliers (numeric only)
        if issue_type in ['outliers', 'all'] and pd.api.types.is_numeric_dtype(col_data):
            try:
                numeric_data = col_data.dropna()
                Q1 = numeric_data.quantile(0.25)
                Q3 = numeric_data.quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - QUALITY_THRESHOLDS['outlier_threshold'] * IQR
                upper = Q3 + QUALITY_THRESHOLDS['outlier_threshold'] * IQR
                
                # Align mask with original index
                is_outlier = (col_data < lower) | (col_data > upper)
                mask |= is_outlier
            except Exception:
                pass
                
        return self.df[mask].copy()
