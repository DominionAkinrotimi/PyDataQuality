"""
Example 06: Custom Rules with YAML
Demonstrates using custom validation rules from YAML files.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def main():
    print("Custom YAML Rules Example")
    print("="*60)
    
    # Create sample YAML rules file
    yaml_content = """
thresholds:
  missing_critical: 0.2
  missing_warning: 0.05
  outlier_threshold: 2.0

column_rules:
  age:
    min: 0
    max: 120
  salary:
    min: 0
    max: 1000000
"""
    
    # Save YAML file
    with open('custom_rules.yaml', 'w') as f:
        f.write(yaml_content)
    
    print("\nCreated custom_rules.yaml")
    
    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        'employee_id': range(1, 51),
        'age': np.concatenate([np.random.randint(25, 65, 48), [150, -5]]),
        'salary': np.random.randint(30000, 150000, 50),
        'department': np.random.choice(['Sales', 'Engineering', 'HR'], 50)
    })
    
    # Load custom rules
    print("\nLoading custom rules...")
    rules = pdq.load_rules_from_yaml('custom_rules.yaml')
    
    # Analyze with custom rules
    print("\nAnalyzing with custom rules...")
    analyzer = pdq.DataQualityAnalyzer(df, name="Employee Data", rules=rules)
    
    # Generate report
    pdq.generate_report(analyzer, output_path="custom_rules_report.html")
    
    print("\nReport generated: custom_rules_report.html")
    print(f"Found {len(analyzer.issues)} quality issues using custom rules")
    
    # Cleanup
    os.remove('custom_rules.yaml')
    
    print("\n" + "="*60)
    print("Example complete!")

if __name__ == "__main__":
    main()
