# pydataquality/config.py
"""
Configuration settings for PyDataQuality module.
"""

# Visualization settings
VISUAL_CONFIG = {
    'figure_size': (12, 8),
    'dpi': 100,
    'color_palette': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
    'missing_color': '#d62728',
    'valid_color': '#2ca02c',
    'warning_color': '#ff7f0e',
    'heatmap_cmap': 'RdYlBu_r',
    'correlation_cmap': 'coolwarm',
}

# Quality check thresholds
QUALITY_THRESHOLDS = {
    'missing_critical': 0.3,      # >30% missing = critical
    'missing_warning': 0.05,      # >5% missing = warning
    'outlier_threshold': 1.5,     # IQR multiplier
    'skew_threshold': 1.0,        # Absolute skewness > 1 = skewed
    'unique_threshold': 0.01,     # Unique values < 1% of rows
    'zero_threshold': 0.8,        # >80% zeros = suspicious
}

# Report settings
REPORT_CONFIG = {
    'max_columns_display': 10,
    'max_categories_display': 15,
    'sample_size': 1000,
    'round_decimals': 4,
}