# tests/test_pydataquality.py
"""
Unit tests for PyDataQuality.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pydataquality as pdq


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    np.random.seed(42)
    data = {
        'id': range(100),
        'numeric_col': np.random.normal(0, 1, 100),
        'categorical_col': np.random.choice(['A', 'B', 'C'], 100),
        'date_col': pd.date_range('2020-01-01', periods=100, freq='D'),
        'missing_col': [np.nan if i % 10 == 0 else i for i in range(100)],
    }
    return pd.DataFrame(data)


def test_analyzer_initialization(sample_dataframe):
    """Test DataQualityAnalyzer initialization."""
    analyzer = pdq.DataQualityAnalyzer(sample_dataframe, "Test Dataset")
    
    assert analyzer.name == "Test Dataset"
    assert len(analyzer.column_stats) == 5
    assert analyzer.dataset_stats['rows'] == 100
    assert analyzer.dataset_stats['columns'] == 5


def test_quick_quality_check(sample_dataframe):
    """Test quick_quality_check function."""
    summary = pdq.quick_quality_check(sample_dataframe, "Test")
    
    assert 'dataset' in summary
    assert 'issues_by_severity' in summary
    assert 'missing_data_overview' in summary


def test_detect_column_types(sample_dataframe):
    """Test column type detection."""
    column_types = pdq.detect_column_types(sample_dataframe)
    
    assert 'numeric' in column_types
    assert 'categorical' in column_types
    assert 'datetime' in column_types
    assert 'numeric_col' in column_types['numeric']
    assert 'categorical_col' in column_types['categorical']


def test_sample_dataframe():
    """Test dataframe sampling."""
    df = pd.DataFrame({'col': range(1000)})
    sampled = pdq.sample_dataframe(df, n_samples=100)
    
    assert len(sampled) == 100
    assert set(sampled['col']).issubset(set(df['col']))


def test_format_memory_size():
    """Test memory size formatting."""
    assert pdq.format_memory_size(1024) == "1.00 KB"
    assert pdq.format_memory_size(1024 * 1024) == "1.00 MB"
    assert pdq.format_memory_size(500) == "500.00 B"


def test_validate_thresholds():
    """Test threshold validation."""
    user_thresholds = {'missing_critical': 0.4, 'invalid_threshold': 0.9}
    validated = pdq.validate_thresholds(user_thresholds)
    
    assert validated['missing_critical'] == 0.4
    assert 'invalid_threshold' not in validated
    assert validated['missing_warning'] == 0.05  # Default value


def test_find_duplicate_columns():
    """Test duplicate column detection."""
    df = pd.DataFrame({
        'col1': range(100),
        'col2': range(100),  # Perfect duplicate
        'col3': np.random.normal(0, 1, 100),  # Different
    })
    
    duplicates = pdq.find_duplicate_columns(df, threshold=0.99)
    
    # col1 and col2 should be detected as duplicates
    assert len(duplicates) == 1
    assert 'col1' in duplicates[0]
    assert 'col2' in duplicates[0]


def test_detect_potential_ids():
    """Test ID column detection."""
    df = pd.DataFrame({
        'id': range(100),
        'customer_id': range(100, 200),
        'name': [f'Customer_{i}' for i in range(100)],
    })
    
    potential_ids = pdq.detect_potential_ids(df)
    
    assert len(potential_ids) == 2
    ids_found = [info['column'] for info in potential_ids]
    assert 'id' in ids_found
    assert 'customer_id' in ids_found


def test_issue_severity_calculation(sample_dataframe):
    """Test that issues are correctly categorized by severity."""
    analyzer = pdq.DataQualityAnalyzer(sample_dataframe, "Test")
    
    # Introduce a critical issue (>30% missing)
    df_with_critical = sample_dataframe.copy()
    df_with_critical['critical_missing'] = [np.nan] * 40 + [1] * 60
    
    analyzer_critical = pdq.DataQualityAnalyzer(df_with_critical, "Test Critical")
    
    critical_found = False
    for issue in analyzer_critical.issues:
        if issue.severity == 'critical' and 'missing' in issue.issue_type.lower():
            critical_found = True
            break
    
    assert critical_found, "Should detect critical missing values"


def test_report_generation(sample_dataframe):
    """Test report generation in different formats."""
    analyzer = pdq.DataQualityAnalyzer(sample_dataframe, "Test Report")
    
    # Test HTML report
    html_report = pdq.generate_report(analyzer, format='html')
    assert isinstance(html_report, str)
    assert '<html>' in html_report.lower()
    
    # Test text report
    text_report = pdq.generate_report(analyzer, format='text')
    assert isinstance(text_report, str)
    assert 'DATA QUALITY ANALYSIS REPORT' in text_report
    
    # Test JSON report
    json_report = pdq.generate_report(analyzer, format='json')
    assert isinstance(json_report, str)
    assert 'dataset' in json_report


def test_visualizer_creation(sample_dataframe):
    """Test visualizer creation."""
    analyzer = pdq.DataQualityAnalyzer(sample_dataframe, "Test Visual")
    visualizer = pdq.DataQualityVisualizer(analyzer)
    
    # Test creating a specific visualization
    fig = visualizer.create_missing_values_matrix()
    assert fig is not None
    
    # Test comprehensive report
    figures = visualizer.create_comprehensive_report()
    assert isinstance(figures, dict)
    assert len(figures) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])