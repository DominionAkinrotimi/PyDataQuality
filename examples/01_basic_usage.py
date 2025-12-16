# examples/01_basic_usage.py
"""
Basic usage examples for PyDataQuality.
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Import the module
import sys
sys.path.append('..')  # Add parent directory to path
import pydataquality as pdq

print("PyDataQuality Basic Usage Examples")
print("=" * 60)

# Example 1: Load sample data
print("\n1. Loading sample data...")
titanic = sns.load_dataset('titanic')
print(f"   Titanic dataset: {titanic.shape[0]} rows, {titanic.shape[1]} columns")

# Example 2: Quick quality check
print("\n2. Quick quality check...")
summary = pdq.quick_quality_check(titanic, name="Titanic Dataset")

# Example 3: Comprehensive analysis
print("\n3. Comprehensive analysis...")
analyzer = pdq.analyze_dataframe(titanic, name="Titanic Dataset", verbose=True)

# Example 4: Get detailed column report
print("\n4. Detailed column report for 'age'...")
age_report = analyzer.get_column_report('age')
if age_report:
    print(f"   Column: {age_report['name']}")
    print(f"   Missing values: {age_report['missing_percentage']:.1f}%")
    print(f"   Issues found: {len(age_report['issues'])}")
    for issue in age_report['issues']:
        print(f"     - [{issue['severity'].upper()}] {issue['message']}")

# Example 5: Generate visualizations
print("\n5. Creating visualizations...")
plt.figure(figsize=(12, 8))
visualizer = pdq.create_visual_report(analyzer, show_plots=True)

# Example 6: Generate HTML report
print("\n6. Generating HTML report...")
html_report = pdq.generate_report(analyzer, format='html')
with open("titanic_quality_report.html", "w", encoding='utf-8') as f:
    f.write(html_report)
print("   Report saved to 'titanic_quality_report.html'")

print("\n" + "=" * 60)
print("Basic examples completed successfully!")