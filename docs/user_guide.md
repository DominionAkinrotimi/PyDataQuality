# User Guide

Welcome to PyDataQuality! This guide is designed for users of all levels, from beginners running their first check to enterprise engineers building data pipelines.

## 1. Choose Your Environment

PyDataQuality works where you work. Choose the method that fits your current task:

| Environment | Best For... | Recommended Command |
| :--- | :--- | :--- |
| **Command Line (CLI)** | Quick checks on CSV files without writing code. ideal for non-programmers or quick audits. | `python cli.py data.csv` |
| **Jupyter / Colab** | Interactive exploration, visual debugging, and data science workflows. | `pdq.show_report(analyzer)` |
| **Python Script** | Automated pipelines, airflow DAGs, or production software. | `pdq.generate_report(...)` |

---

## 2. Step-by-Step Usage

### A. The Interactive Notebook User (Jupyter/Colab/Kaggle)
*Goal: I have a dataframe and I want to see what's wrong with it.*

1.  **Import**: `import pydataquality as pdq`
2.  **Load**: `df = pd.read_csv("my_data.csv")`
3.  **Analyze & View**:
    ```python
    # Run analysis
    analyzer = pdq.analyze_dataframe(df)

    # Display interactive dashboard directly in the cell
    pdq.show_report(analyzer)
    ```
    *Result*: A scrolling HTML dashboard appears right in your notebook.

### B. The Script / Pipeline User
*Goal: I want to save a report to disk automatically every night.*

1.  **Analyze**:
    ```python
    analyzer = pdq.analyze_dataframe(df)
    ```
2.  **Save Report**:
    ```python
    # Save as independent HTML file (easy to email or host)
    pdq.generate_report(analyzer, output_path="daily_report.html")
    ```
    *Result*: A `daily_report.html` file is created.

### C. The Command Line User
*Goal: I just downloaded `data.csv` and want to check quality instantly.*

1.  **Open Terminal**.
2.  **Run**:
    ```bash
    python cli.py data.csv --output report.html
    ```
    *Result*: The tool reads the file, calculates stats, and saves `report.html`.

---

## 3. Function Cookbook (When to use what?)

### Core Functions

| Function | When to use it | Expected Output |
| :--- | :--- | :--- |
| `analyze_dataframe(df)` | **Always**. This is the first step. It runs all the math. | An `Analyzer` object containing all stats. |
| `quick_quality_check(df)` | When you just want to print a summary to the console (no HTML). | None (Prints text to screen). |
| `show_report(analyzer)` | In **Jupyter/Colab** only. | Displays HTML dashboard in output cell. |
| `generate_report(analyzer)` | When you need to **save** the file to share later. | A `.html` or `.txt` file on disk. |

### Utilities (Combine these!)

**Scenario: "My file is too big (1GB+)"**
*Combine `sample_large_dataset` + `analyze_dataframe`*
```python
# 1. Sample it first (Smart batching)
df_small = pdq.sample_large_dataset("big_file.csv", n_samples=10000)
# 2. Analyze the sample
analyzer = pdq.analyze_dataframe(df_small)
```

**Scenario: "I need to check for changes since last week"**
*Combine `compare_reports`*
```python
# Compare two analyzers
drift_df = pdq.compare_reports(analyzer_old, analyzer_new)
print(drift_df)
```

---

## 5. Advanced Workflows

### Extracting Bad Data for Remediation
You found 500 outliers in 'Age'. Now what? required to fix them?
Use `get_problematic_rows` to extract them into a new dataframe for cleaning.

```python
# 1. Identify issues
analyzer = pdq.analyze_dataframe(df)

# 2. Extract rows with invalid ages
bad_age_rows = analyzer.get_problematic_rows('Age', issue_type='outliers')

# 3. Inspect or Fix
print(f"Found {len(bad_age_rows)} bad rows")
bad_age_rows.to_csv("ages_to_fix.csv")
```

### Supported File Formats
PyDataQuality supports any format pandas can read.
*   **CLI**: Auto-detects `.csv`, `.xlsx`, `.xls`, `.json`, `.parquet`.
*   **Python**: Pass any pandas DataFrame (read from SQL, API, Snowflake, etc.).

---

## 6. Troubleshooting & FAQ

### How to Fix Common Errors

**Error: "MemoryError" or "Kernel Died"**
*   **Why**: Your dataset is too big for your computer's RAM.
*   **Fix**: Do not read the whole file. Use `pdq.sample_large_dataset('file.csv')` instead of `pd.read_csv()`.

**Error: "Visualizations check failed"**
*   **Why**: You might be on a server without a screen (headless).
*   **Fix**: The library handles this automatically, but if you see issues, try `analyzer = pdq.analyze_dataframe(df)` (without extra plotting commands) first.

**Error: "Stratified sampling failed"**
*   **Why**: You tried to stratify by a column like "ID" that is unique for every row.
*   **Fix**: Only stratify by "Category", "Region", or "Status" columns (few unique values).

**Question: Can I use this with Excel?**
*   **Yes**: Just read it with pandas first: `df = pd.read_excel("data.xlsx")`, then pass `df` to PyDataQuality.
