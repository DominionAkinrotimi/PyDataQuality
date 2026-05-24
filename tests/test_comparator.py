import pytest
import pandas as pd
import numpy as np
import pydataquality as pdq
from pydataquality.comparator import DataQualityComparator, compare_drift

def test_comparator_psi_numerical():
    """Test PSI calculation for numerical columns."""
    np.random.seed(42)
    # Stable distribution (both normal with mean 0, std 1)
    ref_df = pd.DataFrame({'num': np.random.normal(0, 1, 1000)})
    curr_df_stable = pd.DataFrame({'num': np.random.normal(0, 1, 1000)})
    
    ref_analyzer = pdq.analyze_dataframe(ref_df)
    curr_analyzer_stable = pdq.analyze_dataframe(curr_df_stable)
    
    comparator_stable = DataQualityComparator(ref_analyzer, curr_analyzer_stable)
    psi_stable = comparator_stable.calculate_psi('num')
    
    # PSI for identical distributions should be very low (< 0.1)
    assert psi_stable < 0.1
    
    # Drifing distribution (current is shifted: mean 1.5, std 1)
    curr_df_drift = pd.DataFrame({'num': np.random.normal(1.5, 1, 1000)})
    curr_analyzer_drift = pdq.analyze_dataframe(curr_df_drift)
    
    comparator_drift = DataQualityComparator(ref_analyzer, curr_analyzer_drift)
    psi_drift = comparator_drift.calculate_psi('num')
    
    # PSI for shifted distributions should be high (>= 0.25)
    assert psi_drift >= 0.25

def test_comparator_psi_categorical():
    """Test PSI calculation for categorical columns."""
    ref_df = pd.DataFrame({'cat': ['A'] * 500 + ['B'] * 300 + ['C'] * 200})
    
    # Stable: same proportions
    curr_df_stable = pd.DataFrame({'cat': ['A'] * 490 + ['B'] * 310 + ['C'] * 200})
    # Drifted: totally different proportions
    curr_df_drift = pd.DataFrame({'cat': ['A'] * 100 + ['B'] * 200 + ['C'] * 700})
    
    ref_analyzer = pdq.analyze_dataframe(ref_df)
    curr_analyzer_stable = pdq.analyze_dataframe(curr_df_stable)
    curr_analyzer_drift = pdq.analyze_dataframe(curr_df_drift)
    
    comparator_stable = DataQualityComparator(ref_analyzer, curr_analyzer_stable)
    psi_stable = comparator_stable.calculate_psi('cat')
    assert psi_stable < 0.1
    
    comparator_drift = DataQualityComparator(ref_analyzer, curr_analyzer_drift)
    psi_drift = comparator_drift.calculate_psi('cat')
    assert psi_drift >= 0.25

def test_comparator_ks_test():
    """Test Kolmogorov-Smirnov test statistics and fallback."""
    np.random.seed(42)
    ref_df = pd.DataFrame({'num': np.random.normal(0, 1, 500)})
    curr_df_stable = pd.DataFrame({'num': np.random.normal(0, 1, 500)})
    curr_df_drift = pd.DataFrame({'num': np.random.normal(2.0, 1, 500)})
    
    ref_analyzer = pdq.analyze_dataframe(ref_df)
    curr_analyzer_stable = pdq.analyze_dataframe(curr_df_stable)
    curr_analyzer_drift = pdq.analyze_dataframe(curr_df_drift)
    
    comparator_stable = DataQualityComparator(ref_analyzer, curr_analyzer_stable)
    ks_stable = comparator_stable.calculate_ks('num')
    
    # Same distribution: low D statistic, high p-value (not significant)
    assert ks_stable['statistic'] < 0.15
    assert ks_stable['p_value'] > 0.05
    
    comparator_drift = DataQualityComparator(ref_analyzer, curr_analyzer_drift)
    ks_drift = comparator_drift.calculate_ks('num')
    
    # Different distribution: high D statistic, extremely low p-value (< 0.05)
    assert ks_drift['statistic'] > 0.5
    assert ks_drift['p_value'] < 0.01

def test_compare_distributions_summary():
    """Test the complete compare_distributions overview DataFrame."""
    np.random.seed(42)
    ref_df = pd.DataFrame({
        'stable_num': np.random.normal(0, 1, 500),
        'drift_num': np.random.normal(0, 1, 500),
        'stable_cat': ['A'] * 250 + ['B'] * 250
    })
    curr_df = pd.DataFrame({
        'stable_num': np.random.normal(0, 1, 500),
        'drift_num': np.random.normal(2.5, 1, 500), # significant drift
        'stable_cat': ['A'] * 260 + ['B'] * 240
    })
    
    ref_analyzer = pdq.analyze_dataframe(ref_df)
    curr_analyzer = pdq.analyze_dataframe(curr_df)
    
    drift_df = compare_drift(ref_analyzer, curr_analyzer)
    
    assert isinstance(drift_df, pd.DataFrame)
    assert len(drift_df) == 3
    assert set(drift_df['column']) == {'stable_num', 'drift_num', 'stable_cat'}
    
    # Check drift status
    drift_num_status = drift_df.loc[drift_df['column'] == 'drift_num', 'drift_status'].values[0]
    stable_num_status = drift_df.loc[drift_df['column'] == 'stable_num', 'drift_status'].values[0]
    
    assert drift_num_status == 'significant'
    assert stable_num_status == 'stable'
