# PyDataQuality API Reference

This document provides detailed information about all classes, functions, and methods available in PyDataQuality.

## Core Classes

### DataQualityAnalyzer

The main analysis class that performs comprehensive data quality assessment.

#### Constructor
```python
DataQualityAnalyzer(df: pandas.DataFrame, name: str = "Dataset")
```

**Parameters:**
- `df`: Input pandas DataFrame to analyze
- `name`: Name of the dataset for reporting purposes

**Attributes:**
- `df`: Copy of the input DataFrame
- `name`: Dataset name
- `issues`: List of `QualityIssue` objects found during analysis
- `column_stats`: Dictionary mapping column names to `ColumnStats` objects
- `dataset_stats`: Dictionary with dataset-level statistics

#### Methods

##### `get_summary() -> Dict`
Returns a comprehensive summary of the analysis results.

**Returns:**
```python
{
    'dataset': {
        'name': str,
        'rows': int,
        'columns': int,
        'total_cells': int,
        'memory_usage_mb': float,
        'analysis_timestamp': str
    },
    'columns': int,
    'issues_by_severity': {'critical': int, 'warning': int, 'info': int},
    'issues_by_type': Dict[str, int],
    'column_types': Dict[str, int],
    'missing_data_overview': {
        'columns_with_missing': int,
        'total_missing_cells': int,
        'total_missing_percentage': float,
        'columns': List[Dict]  # Top columns with missing values
    }
}
```

##### `analyzer.get_column_report(column)`
Returns a dictionary containing detailed statistics and issues for a single column.

##### `analyzer.get_problematic_rows(column, issue_type='all')`
Returns a pandas DataFrame containing only the rows that failed quality checks for the specified column.

**Parameters:**
- `column` (str): Name of the column.
- `issue_type` (str): Type of issue filters. Options: `'missing_values'`, `'outliers'`, `'all'`.

**Returns:**
- `pd.DataFrame`: Subset of the original dataframe.

**Example:**
```python
# Get all rows where 'age' is missing or an outlier
bad_data = analyzer.get_problematic_rows('age')

# Get only rows where 'salary' is an outlier
outliers = analyzer.get_problematic_rows('salary', issue_type='outliers')
```



---

### QualityIssue Dataclass

Represents a single data quality issue.

```python
@dataclass
class QualityIssue:
    column: str
    issue_type: str
    severity: str  # 'critical', 'warning', 'info'
    message: str
    affected_count: int = 0
    affected_percentage: float = 0.0
    details: Dict = field(default_factory=dict)
```

---

### ColumnStats Dataclass

Stores statistics for a single column.

```python
@dataclass
class ColumnStats:
    name: str
    dtype: str
    total_count: int
    missing_count: int = 0
    missing_percentage: float = 0.0
    unique_count: int = 0
    stats: Dict = field(default_factory=dict)
```

---

## DataQualityVisualizer

Creates visualizations from data quality analysis results.

#### Constructor
```python
DataQualityVisualizer(analyzer: DataQualityAnalyzer)
```

**Parameters:**
- `analyzer`: A `DataQualityAnalyzer` instance with analysis results

#### Methods

##### `create_missing_values_matrix(figsize: Tuple = None) -> matplotlib.figure.Figure`
Creates a heatmap showing missing value patterns across the dataset.

##### `create_issues_summary_chart(figsize: Tuple = None) -> matplotlib.figure.Figure`
Creates bar charts showing issues by severity and type.

##### `create_missing_values_distribution(figsize: Tuple = None) -> matplotlib.figure.Figure`
Creates a bar chart showing missing values per column.

##### `create_numeric_distributions(columns: List[str] = None, figsize: Tuple = None) -> matplotlib.figure.Figure`
Creates distribution plots for numeric columns.

##### `create_outlier_detection_plot(columns: List[str] = None, figsize: Tuple = None) -> matplotlib.figure.Figure`
Creates boxplots for outlier detection.

##### `create_correlation_heatmap(figsize: Tuple = None) -> matplotlib.figure.Figure`
Creates correlation heatmap for numeric columns.

##### `create_categorical_analysis(columns: List[str] = None, figsize: Tuple = None) -> matplotlib.figure.Figure`
Creates bar plots for categorical column analysis.

##### `create_comprehensive_report(save_path: str = None) -> Dict[str, matplotlib.figure.Figure]`
Creates all visualizations and optionally saves them.

---

## QualityReportGenerator

Generates formatted reports from analysis results.

#### Constructor
```python
QualityReportGenerator(analyzer: DataQualityAnalyzer)
```

#### Methods

##### `generate_text_report() -> str`
Generates a detailed text report.

##### `generate_html_report(include_visuals: bool = False) -> str`
Generates an HTML report with optional visualizations.

##### `save_report(output_path: str, format: str = 'html')`
Saves report to file in specified format ('html', 'text', 'json').

---

## Main Module Functions

### `analyze_dataframe(df, name="Dataset", verbose=True) -> DataQualityAnalyzer`
Perform comprehensive data quality analysis on a DataFrame.

**Parameters:**
- `df`: pandas.DataFrame to analyze
- `name`: Name of the dataset for reporting
- `verbose`: Whether to print progress information

**Returns:** `DataQualityAnalyzer` instance

### `create_visual_report(analyzer, save_dir=None, show_plots=True) -> DataQualityVisualizer`
Create visualizations from data quality analysis.

**Parameters:**
- `analyzer`: `DataQualityAnalyzer` instance
- `save_dir`: Directory to save visualization files
- `show_plots`: Whether to display plots immediately

**Returns:** `DataQualityVisualizer` instance

### `generate_report(analyzer, output_path=None, format='html') -> Union[str, None]`
Generate a formatted report from analysis results.

**Parameters:**
- `analyzer`: `DataQualityAnalyzer` instance
- `output_path`: Path to save the report file (if None, returns content)
- `format`: Report format ('html', 'text', 'json')

**Returns:** Report content if `output_path` is None, otherwise None

### `quick_quality_check(df, name="Dataset") -> Dict`
Perform a quick data quality check with summary output.

**Parameters:**
- `df`: pandas.DataFrame to analyze
- `name`: Name of the dataset

**Returns:** Summary dictionary

---

## Utility Functions

### `detect_column_types(df: pandas.DataFrame) -> Dict[str, List[str]]`
Detect and categorize columns by their data types.

**Returns:** Dictionary with column type categories as keys and lists of column names as values.

### `sample_dataframe(df: pandas.DataFrame, n_samples: int = 1000, random_state: int = 42) -> pandas.DataFrame`
Sample rows from dataframe for faster analysis.

### `validate_thresholds(thresholds: Dict[str, float]) -> Dict[str, float]`
Validate and provide default thresholds for quality checks.

### `format_memory_size(bytes: float) -> str`
Format memory size in human-readable format.

### `create_summary_statistics(df: pandas.DataFrame) -> Dict[str, Any]`
Create basic summary statistics for a dataframe.

### `find_duplicate_columns(df: pandas.DataFrame, threshold: float = 0.95) -> List[List[str]]`
Find columns with high correlation or similarity.

### `detect_potential_ids(df: pandas.DataFrame) -> List[Dict]`
Detect columns that might be ID columns.

### `check_date_consistency(df: pandas.DataFrame, date_columns: List[str]) -> Dict[str, Any]`
Check consistency of date columns.

---

## Configuration

### `pydataquality.config.VISUAL_CONFIG`
Dictionary containing visualization settings:
```python
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
```

### `pydataquality.config.QUALITY_THRESHOLDS`
Dictionary containing quality check thresholds:
```python
QUALITY_THRESHOLDS = {
    'missing_critical': 0.3,      # >30% missing = critical
    'missing_warning': 0.05,      # >5% missing = warning
    'outlier_threshold': 1.5,     # IQR multiplier
    'skew_threshold': 1.0,        # Absolute skewness > 1 = skewed
    'unique_threshold': 0.01,     # Unique values < 1% of rows
    'zero_threshold': 0.8,        # >80% zeros = suspicious
}
```

### `pydataquality.config.REPORT_CONFIG`
Dictionary containing report settings:
```python
REPORT_CONFIG = {
    'max_columns_display': 10,
    'max_categories_display': 15,
    'sample_size': 1000,
    'round_decimals': 4,
}
```

---

## Error Handling

All functions include error handling for common issues:

1. **Invalid DataFrame**: Raises `TypeError` if input is not a pandas DataFrame
2. **Missing Columns**: Returns `None` or empty results for non-existent columns
3. **Invalid Parameters**: Uses default values and issues warnings for invalid parameters
4. **File I/O Errors**: Raises appropriate exceptions with descriptive messages

---

## Examples

For detailed usage examples, see the `examples` directory:
# PyDataQuality Example Files

| #   | Filename                     | Description                                                   |
|-----|------------------------------|---------------------------------------------------------------|
| 01  | 01_basic_usage.py            | Quick start guide - basic analysis and report generation      |
| 02  | 02_advanced_features.py      | Advanced configurations, custom thresholds, multiple report formats |
| 03  | 03_interactive_notebook.py   | Jupyter/Colab notebook usage demonstration                    |
| 04  | 04_pdf_report_example.py     | PDF export demonstration with professional theme              |
| 05  | 05_interactive_notebook.py   | Interactive report display in notebooks                       |
| 06  | 06_custom_yaml_rules.py      | Custom validation rules from YAML files                       |
| 07  | 07_batch_sampling.py         | Efficient sampling from large CSV files (100K+ rows)          |
| 08  | 08_data_extraction.py        | Extracting problematic rows for remediation                   |
| 09  | 09_full_system_simulation.py | Multi-persona testing (Data Scientist, Engineer, CLI User)    |
| 10  | 10_debug_details.py          | Details column verification and debugging                     |
| 11  | 11_verify_new_features.py    | Feature verification for `get_problematic_rows()`             |
| 12  | 12_test_all_formats.py       | Multi-format support testing (CSV, Excel, JSON, Parquet)      |
| 13  | 13_pdf_export_demo.py        | PDF export demonstration                                      |
| 14  | 14_professional_pdf_report.py| Professional theme report generation                          |
