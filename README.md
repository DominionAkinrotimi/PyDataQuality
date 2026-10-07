# PyDataQuality

**Find out what is wrong with a dataset, and get the rows to fix, in one line of Python.**

PyDataQuality automates the tedious 80% of data science: validating, profiling, and cleaning new datasets. It transforms raw pandas DataFrames into publication-ready quality reports with a single line of code. It also samples large files, applies your own validation rules, compares two datasets for drift, and writes a prompt you can hand to an AI assistant to get cleaning code.

![Data Quality Analysis](https://raw.githubusercontent.com/DominionAkinrotimi/pydataquality/main/docs/images/sample_visualization.png)

## Features

### Core Capabilities
- **Data Quality Analysis**: Detect missing values, outliers, inconsistencies, and data type issues
- **Data Extraction**: Pinpoint and extract problematic rows (e.g., specific outliers) for remediation via `get_problematic_rows()`
- **Multi-Format Support**: Native support for CSV, Excel (.xlsx, .xls), JSON, and Parquet files
- **CLI Interface**: Auto-detects file formats from the terminal - no coding required
- **Interactive Notebook Display**: Direct rendering in Jupyter/Colab with `show_report()`
- **Batch Sampling**: Process large datasets (GBs) efficiently with chunk-based sampling
- **Custom YAML Rules**: Per-column rules (`min`, `max`, `allowed_values`, `unique`, `not_null`) loaded from a YAML file
- **Duplicate Detection**: Exact duplicate rows are reported
- **Drift Detection**: Population Stability Index and KS test between two datasets via `compare_drift()`
- **AI Remediation Prompts**: A ready-to-paste prompt describing the issues. Raw values from columns that look like personal data are left out by default
- **Comprehensive Visualizations**: Publication-quality plots for data quality assessment
- **Professional Reports**: HTML, text, and JSON reports with actionable insights
- **Easy Integration**: Works seamlessly with pandas DataFrames from any source

### Supported Input Formats
**CLI**: Auto-detects CSV, Excel (.xlsx, .xls), JSON, Parquet (`python -m pydataquality data.csv`)  
**Python API**: Accepts any pandas DataFrame from:
- CSV files (`pd.read_csv()`)
- Excel files (`pd.read_excel()`)
- JSON files (`pd.read_json()`)
- Parquet files (`pd.read_parquet()`)
- SQL databases (`pd.read_sql()`)
- APIs (any source that produces a DataFrame)
- Cloud platforms (Snowflake, BigQuery, etc.)

**Summary**: PyDataQuality works with CSV, Excel, JSON, Parquet files, and any pandas DataFrame from SQL databases, APIs, or cloud platforms. The library is format-agnostic - it only requires a pandas DataFrame as input.

## Why PyDataQuality?

### The Problem
You just received a new dataset. You need to know what's wrong with it and how to fix it - **fast**. Existing tools either:
- Produce a long report to read rather than a list of things to fix (ydata-profiling, now fg-data-profiling)
- Require setup before the first result (Great Expectations: data contexts, expectation suites, checkpoints)
- Don't give actionable insights (pandas `.describe()`: just basic stats)

### The Solution
PyDataQuality fills the gap between "too simple" and "too complex":

> **"I just got a new dataset. What's wrong with it, and how do I fix it? I need answers in 30 seconds, not 30 minutes."**

### Comparison with Alternatives

| | ydata-profiling | Great Expectations | **PyDataQuality** |
|:--------|:-----------------|:-------------------|:------------------|
| Result without any configuration | ✅ | ❌ | ✅ |
| Returns the problem rows as a DataFrame | ❌ | ✅ (per expectation) | ✅ |
| Command line tool | ✅ | ✅ | ✅ |
| You write the rules yourself | Not applicable | Required | Optional |
| Depth of profiling and number of checks | Highest | Highest | Basic |
| Exit code to stop a pipeline | ❌ | ✅ | ✅ (`--fail-on`) |

Those projects do far more than PyDataQuality. Use them when you need exhaustive profiling or a managed set of expectations. Use this when you want a short answer quickly.

### Real-World Example

**Scenario**: Data scientist gets a CSV with 1M rows

```python
analyzer = pdq.analyze_dataframe(df)
bad_ages = analyzer.get_problematic_rows('age', 'outliers')
bad_ages.to_csv('fix_these.csv')  # Send to data team
```

**Bottom line**: PyDataQuality is **simple by design**. It just works, without making you read 50 pages of documentation.

## Installation

```bash
pip install pydataquality

# For interactive notebook support (Jupyter/Colab)
pip install "pydataquality[notebook]"
```

To work on the library itself:

```bash
git clone https://github.com/DominionAkinrotimi/pydataquality.git
cd pydataquality
pip install -e ".[dev]"
pytest
```

## Quick Start

```python
import pandas as pd
import pydataquality as pdq

# Load your data
df = pd.read_csv('your_data.csv')

# Quick quality check
summary = pdq.quick_quality_check(df, name="My Dataset")

# Comprehensive analysis
analyzer = pdq.analyze_dataframe(df, name="My Dataset")

# Analysis with custom thresholds (e.g., stricter missing data check)
# Analysis with custom thresholds and excluded values
config = {
    'missing_critical': 0.1, 
    'outlier_threshold': 2.0,
    'exclude_values': {
        'age': [150, -5],  # specific values to ignore
        'sales': [-100]
    }
}
analyzer = pdq.analyze_dataframe(df, name="My Dataset", config=config)

# Generate visualizations
visualizer = pdq.create_visual_report(analyzer)

# Generate HTML report
pdq.generate_report(analyzer, output_path="quality_report.html", format='html')

# Get AI assistance for fixes (includes EDA context by default)
prompt = pdq.generate_ai_prompt(analyzer)
print(prompt) 

# Output example:
# "I have a dataset with 1000 rows. Issues: age (outliers: outside [18, 65]).
#  Statistical Context: age (int64): Mean=42, Max=150...
#  Please write a script..."
```

## CLI Usage

Run the analysis directly from your terminal:

```bash
# Basic usage (CSV, Excel, JSON and Parquet are detected from the extension)
pydataquality data.csv

# Generate professional HTML report
pydataquality data.csv --report html --theme professional

# Create visualizations
pydataquality data.csv --visualize

# Apply your own rules and stop a pipeline when they fail (exit code 2)
pydataquality data.csv --rules rules.yaml --fail-on critical
```

`python -m pydataquality` works the same way.

### Custom rules

```yaml
# rules.yaml
thresholds:
  missing_critical: 0.2
column_rules:
  age:
    min: 0
    max: 120
  status:
    allowed_values: [paid, pending, refunded]
  order_id:
    unique: true
    not_null: true
```

```python
rules = pdq.load_rules_from_yaml("rules.yaml")
analyzer = pdq.analyze_dataframe(df, rules=rules)
bad = analyzer.get_problematic_rows("age", "rule_violation")
```

## Research Paper

PyDataQuality is backed by an academic paper that formally describes its architecture, mathematical foundations, and empirical benchmarks:

> **PyDataQuality: An Actionable, Lightweight Data Profiling and Distribution Drift Detection Framework for Production Machine Learning Pipelines**
> — Dominion Akinrotimi, 2026

The paper covers:
- The five-layer modular architecture
- Formal derivations of Shannon Entropy, IQR (Tukey Fences), PSI, and the KS Test
- Benchmark results showing ~80ms constant-time execution in sampled mode
- An MLOps case study demonstrating drift detection as a model quality gate

📄 [Read the Paper (PDF)](https://github.com/DominionAkinrotimi/PyDataQuality/blob/main/paperwriting/final%20paper%20in%20pdf/PyDataQuality.pdf)

---

## Documentation

- [Quickstart Guide](https://github.com/DominionAkinrotimi/pydataquality/blob/main/docs/quickstart.md)
- [API Reference](https://github.com/DominionAkinrotimi/pydataquality/blob/main/docs/api.md)
- [Examples](https://github.com/DominionAkinrotimi/pydataquality/blob/main/examples/)
- [📚 Technical Study Guide](https://github.com/DominionAkinrotimi/PyDataQuality/blob/main/STUDY_GUIDE.md) — Deep dive into every concept, formula, and design decision behind the library

## Examples

Check the `examples` directory for comprehensive usage examples:

1. **Basic Usage**: Simple analysis and reporting
2. **Advanced Features**: Custom configurations and visualizations
3. **Real-world Scenarios**: Handling various data quality issues


## Project Structure
```
PyDataQuality/
├── pydataquality/       # Main package directory
│   ├── __init__.py      # Exports
│   ├── __main__.py      # Package entry point
│   ├── analyzer.py      # Core analysis engine
│   ├── cli.py           # Package CLI logic
│   ├── comparator.py    # Data drift detection
│   ├── config.py        # Settings management
│   ├── reporter.py      # Report generation
│   ├── utils.py         # Helper functions
│   └── visualizer.py    # Visualization engine
├── docs/                # Documentation
├── examples/            # Usage examples
├── tests/               # Unit tests
├── cli.py               # Root CLI script (local usage)
├── setup.py             # Installation script
└── requirements.txt     # Dependencies
```

## Key Components

### 1. DataQualityAnalyzer
Core analysis engine that examines data structure, detects issues, and computes statistics.

### 2. DataQualityVisualizer
Creates comprehensive visualizations including:
- Missing value heatmaps
- Outlier detection plots
- Distribution analysis
- Correlation heatmaps
- Categorical value distributions

### 3. QualityReportGenerator
Generates professional reports in multiple formats with actionable recommendations.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with pandas, matplotlib, and seaborn
- Inspired by real-world data quality challenges

- Designed for data scientists and analysts





