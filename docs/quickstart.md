# Quickstart Guide for PyDataQuality

## Installation

```bash
# Install from local development
pip install -e .

# Or install requirements directly
pip install pandas numpy matplotlib seaborn jinja2
```

## CLI Usage (No Code Required)

PyDataQuality can be used directly from the terminal to audit files of any format (CSV, Excel, JSON, Parquet).

```bash
# Basic check (generates report.html)
python cli.py data.csv

# Specify output folder
python cli.py data.xlsx --output my_reports/

# Generate JSON report instead of HTML
python cli.py data.parquet --report json

# Full help
python cli.py --help
```

## Basic Usage (Python)

```python
import pandas as pd
import pydataquality as pdq

# Load your data
df = pd.read_csv('your_data.csv')

# 1. Quick quality check (summary only)
summary = pdq.quick_quality_check(df, name="My Dataset")

# 2. Comprehensive analysis
analyzer = pdq.analyze_dataframe(df, name="My Dataset", verbose=True)

# 3. Generate visualizations
visualizer = pdq.create_visual_report(analyzer, show_plots=True)

# 4. Interactive Report (Jupyter/Colab)
pdq.show_report(analyzer, theme='creative')

# 5. Generate HTML file
pdq.generate_report(analyzer, output_path="quality_report.html", format='html')


# 6. Get AI assistance (optional)
prompt = pdq.generate_ai_prompt(analyzer)
print(prompt)  # Copy to ChatGPT/Claude/Gemini for automated fixes
```

## Supported Data Formats

PyDataQuality is **format-agnostic** and works with any pandas DataFrame.

### CLI (Command Line)
Auto-detects file format by extension:
- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- JSON (`.json`)
- Parquet (`.parquet`)

```bash
python cli.py data.csv      # CSV
python cli.py data.xlsx     # Excel
python cli.py data.json     # JSON
python cli.py data.parquet  # Parquet
```

### Python API
Works with DataFrames from **any source**:

```python
import pandas as pd
import pydataquality as pdq

# From CSV
df = pd.read_csv('data.csv')

# From Excel
df = pd.read_excel('data.xlsx')

# From JSON
df = pd.read_json('data.json')

# From Parquet
df = pd.read_parquet('data.parquet')

# From SQL Database
df = pd.read_sql('SELECT * FROM table', connection)

# From API
df = pd.DataFrame(api_response['data'])

# From Cloud (Snowflake, BigQuery, etc.)
df = snowflake_connector.fetch_dataframe(query)

# Analyze any DataFrame
analyzer = pdq.analyze_dataframe(df)
```

**Summary**: PyDataQuality successfully works with:
- CSV files
- Excel files (.xlsx, .xls)
- JSON files
- Parquet files
- Direct DataFrames (SQL, APIs, Cloud platforms, etc.)

## Advanced Usage

### Big Data sampling
```python
# Sample from a 10GB CSV without loading it all
df = pdq.sample_large_dataset("data/huge_file.csv", n_samples=5000)
```

### Custom Rules
```python
rules = pdq.load_rules_from_yaml("quality_rules.yaml")
analyzer = pdq.DataQualityAnalyzer(df, rules=rules)
```

### Data Drift Check
```python
drift_stats = pdq.compare_reports(analyzer_last_week, analyzer_today)
print(drift_stats)
```
```

## Advanced Features

### Access Detailed Column Information

```python
# Get detailed report for a specific column
column_report = analyzer.get_column_report('column_name')

# Get all column statistics
for col_name, stats in analyzer.column_stats.items():
    print(f"{col_name}: {stats.dtype}, Missing: {stats.missing_percentage:.1f}%")
```

### Custom Visualizations

```python
from pydataquality import DataQualityVisualizer

# Create specific visualizations
visualizer = DataQualityVisualizer(analyzer)

# Missing values heatmap
fig1 = visualizer.create_missing_values_matrix()

# Issue summary chart
fig2 = visualizer.create_issues_summary_chart()

# Numeric distributions
fig3 = visualizer.create_numeric_distributions()

# Save visualizations
fig1.savefig('missing_values.png', dpi=150, bbox_inches='tight')
```

### Utility Functions

```python
# Detect column types
column_types = pdq.detect_column_types(df)

# Sample large datasets
sampled_df = pdq.sample_dataframe(df, n_samples=1000)

# Find duplicate columns
duplicates = pdq.find_duplicate_columns(df, threshold=0.95)

# Detect potential ID columns
potential_ids = pdq.detect_potential_ids(df)
```

## Configuration

### Custom Thresholds

```python
from pydataquality.config import QUALITY_THRESHOLDS

# Modify thresholds
QUALITY_THRESHOLDS['missing_critical'] = 0.4  # 40% instead of 30%
QUALITY_THRESHOLDS['outlier_threshold'] = 3.0  # Use 3*IQR for outliers
```

### Visual Configuration

```python
from pydataquality.config import VISUAL_CONFIG

# Customize visual appearance
VISUAL_CONFIG['figure_size'] = (14, 10)
VISUAL_CONFIG['color_palette'] = ['#1a5276', '#229954', '#f39c12', '#e74c3c']
```


## Best Practices

1. **Start with quick_quality_check()** for initial assessment
2. **Use analyze_dataframe()** for comprehensive analysis
3. **Save visualizations** for documentation and sharing
4. **Generate HTML reports** for stakeholder communication
5. **Use sampling** for very large datasets (>1M rows)

## Troubleshooting

**Common Issues:**

1. **Memory Error**: Use `pdq.sample_dataframe()` for large datasets
2. **Slow Performance**: Analyze specific columns instead of entire dataframe
3. **Plot Display Issues**: Save plots to files instead of displaying

**Getting Help:**

- Check the examples directory
- Review the test files for usage patterns

- Examine the generated HTML reports for interpretation guidance
