# examples/03_interactive_notebook.py
"""
Example for Jupyter Notebook usage.
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from IPython.display import display, HTML

# For notebook display
import warnings
warnings.filterwarnings('ignore')

# Import the module
import sys
sys.path.append('..')
import pydataquality as pdq

print("PyDataQuality - Interactive Notebook Example")
print("=" * 70)

# Create a sample dataset with various issues
np.random.seed(42)
data = {
    'customer_id': range(1000),
    'age': np.random.randint(18, 70, 1000),
    'income': np.random.normal(50000, 20000, 1000),
    'purchase_frequency': np.random.poisson(5, 1000),
    'last_login_days': np.random.exponential(30, 1000),
    'region': np.random.choice(['North', 'South', 'East', 'West'], 1000),
    'status': np.random.choice(['Active', 'Inactive', 'Pending'], 1000),
}

df = pd.DataFrame(data)

# Introduce some data quality issues
# Missing values
df.loc[100:150, 'age'] = np.nan
df.loc[200:250, 'income'] = np.nan
df.loc[300:320, 'region'] = None

# Outliers
df.loc[10, 'income'] = 500000  # Extreme outlier
df.loc[20, 'last_login_days'] = 365 * 10  # 10 years ago

# Invalid values
df.loc[400:410, 'age'] = -5  # Negative age
df.loc[420:430, 'age'] = 150  # Unrealistic age

# Inconsistent values
df.loc[500:510, 'region'] = 'north'  # Lowercase
df.loc[520:530, 'region'] = 'SOUTH'  # Uppercase

print(f"Sample dataset created: {df.shape[0]} rows, {df.shape[1]} columns")

# Display sample data
print("\nFirst 5 rows:")
display(df.head())

# Quick quality check
print("\nQuick Quality Check:")
summary = pdq.quick_quality_check(df, name="Customer Data")

# Comprehensive analysis
print("\nComprehensive Analysis:")
analyzer = pdq.analyze_dataframe(df, name="Customer Dataset", verbose=True)

# Display issues found
print("\nCritical Issues Found:")
for issue in analyzer.issues:
    if issue.severity == 'critical':
        print(f"  • {issue.column}: {issue.message}")

# Create visualizations
print("\nCreating Visualizations...")
figures = {}

# Missing values matrix
fig_missing = analyzer.create_missing_values_matrix()
figures['missing_matrix'] = fig_missing
plt.show()

# Issues summary
fig_issues = analyzer.create_issues_summary_chart()
figures['issues_summary'] = fig_issues
plt.show()

# Numeric distributions
fig_dist = analyzer.create_numeric_distributions()
figures['numeric_distributions'] = fig_dist
plt.show()

# Generate HTML report for notebook display
print("\nGenerating HTML Report...")
html_report = pdq.generate_report(analyzer, format='html')
display(HTML(html_report))

# Advanced: Column-specific analysis
print("\nColumn-Specific Analysis:")
for col in ['age', 'income', 'region']:
    report = analyzer.get_column_report(col)
    if report:
        print(f"\n{col}:")
        print(f"  Type: {report['dtype']}")
        print(f"  Missing: {report['missing_percentage']:.1f}%")
        if report['issues']:
            print(f"  Issues: {len(report['issues'])}")
            for issue in report['issues'][:2]:  # Show first 2 issues
                print(f"    • {issue['message']}")

print("\n" + "=" * 70)
print("Analysis complete. Use the generated reports for data quality insights.")