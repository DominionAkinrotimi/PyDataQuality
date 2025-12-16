# examples/02_advanced_features.py
"""
Advanced features and custom configurations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pydataquality as pdq

print("PyDataQuality Advanced Features")
print("=" * 60)

# Create a sample dataset with various data quality issues
print("\n1. Creating synthetic dataset with known issues...")

np.random.seed(42)
n_rows = 1000

data = {
    'customer_id': range(1, n_rows + 1),
    'customer_name': [f'Customer_{i}' for i in range(1, n_rows + 1)],
    'age': np.random.randint(18, 80, n_rows),
    'salary': np.random.normal(50000, 15000, n_rows),
    'purchase_amount': np.random.exponential(100, n_rows),
    'last_purchase_date': [(datetime.now() - timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d') 
                          for _ in range(n_rows)],
    'region': np.random.choice(['North', 'South', 'East', 'West', 'Central'], n_rows),
    'subscription_status': np.random.choice(['Active', 'Inactive', 'Pending', 'Cancelled'], n_rows),
    'email': [f'customer{i}@example.com' for i in range(1, n_rows + 1)],
}

# Introduce some data quality issues
df = pd.DataFrame(data)

# Issue 1: Missing values
df.loc[100:150, 'age'] = np.nan
df.loc[200:250, 'salary'] = np.nan
df.loc[300:320, 'region'] = None

# Issue 2: Outliers
df.loc[10, 'salary'] = 500000  # Extreme outlier
df.loc[20, 'purchase_amount'] = 10000  # Extreme outlier

# Issue 3: Invalid values
df.loc[400:410, 'age'] = -5  # Negative age
df.loc[420:430, 'age'] = 150  # Unrealistic age

# Issue 4: Inconsistent categorical values
df.loc[500:510, 'region'] = 'north'  # Lowercase
df.loc[520:530, 'region'] = 'SOUTH'  # Uppercase
df.loc[540:550, 'region'] = ' East '  # With spaces

# Issue 5: Duplicates
duplicate_rows = df.iloc[600:605].copy()
duplicate_rows['customer_id'] = range(1001, 1006)  # Change IDs to avoid primary key violation
df = pd.concat([df, duplicate_rows], ignore_index=True)

print(f"   Created dataset with {df.shape[0]} rows and {df.shape[1]} columns")

# Example 2: Using utility functions
print("\n2. Using utility functions...")

# Detect column types
column_types = pdq.detect_column_types(df)
print(f"   Column types detected:")
for col_type, columns in column_types.items():
    if columns:
        print(f"     {col_type}: {len(columns)} columns")

# Find potential ID columns
potential_ids = pdq.detect_potential_ids(df)
print(f"\n   Potential ID columns:")
for id_info in potential_ids:
    print(f"     {id_info['column']}: {id_info['uniqueness_ratio']:.1%} unique")

# Example 3: Custom analysis with sampling
print("\n3. Analyzing with sampling for large datasets...")

# Sample the data for faster analysis
sampled_df = pdq.sample_dataframe(df, n_samples=500)
print(f"   Sampled {len(sampled_df)} rows from {len(df)} total rows")

analyzer = pdq.analyze_dataframe(sampled_df, name="Customer Data Sample", verbose=False)

# Example 4: Accessing raw issues and statistics
print("\n4. Accessing detailed analysis results...")

summary = analyzer.get_summary()
print(f"   Total issues found: {sum(summary['issues_by_severity'].values())}")

print(f"\n   Critical issues:")
for issue in analyzer.issues:
    if issue.severity == 'critical':
        print(f"     - {issue.column}: {issue.message}")

# Example 5: Creating specific visualizations
print("\n5. Creating specific visualizations...")
import matplotlib.pyplot as plt

visualizer = pdq.DataQualityVisualizer(analyzer)

# Create missing values matrix
fig1 = visualizer.create_missing_values_matrix()
plt.savefig('missing_values_matrix.png', dpi=150, bbox_inches='tight')
print("   Saved: missing_values_matrix.png")

# Create issues summary
fig2 = visualizer.create_issues_summary_chart()
plt.savefig('issues_summary.png', dpi=150, bbox_inches='tight')
print("   Saved: issues_summary.png")

# Example 6: Generating different report formats
print("\n6. Generating multiple report formats...")

# HTML report
html_report = pdq.generate_report(analyzer, format='html')
with open("customer_data_report.html", "w", encoding='utf-8') as f:
    f.write(html_report)
print("   Generated: customer_data_report.html")

# Text report
text_report = pdq.generate_report(analyzer, format='text')
with open("customer_data_report.txt", "w", encoding='utf-8') as f:
    f.write(text_report)
print("   Generated: customer_data_report.txt")

# JSON report (for programmatic access)
json_report = pdq.generate_report(analyzer, format='json')
with open("customer_data_report.json", "w", encoding='utf-8') as f:
    f.write(json_report)
print("   Generated: customer_data_report.json")

print("\n" + "=" * 60)
print("Advanced examples completed successfully!")