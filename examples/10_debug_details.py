
import pandas as pd
import numpy as np
import sys
import os

# Ensure we import local package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def debug_details():
    print("Generating data with guaranteed issues...")
    
    # 1. Outliers
    df = pd.DataFrame({
        'normal_col': range(100),
        'outlier_col': np.concatenate([np.random.normal(0, 1, 95), [100, 200, 300, 400, 500]])
    })
    
    # 2. Inconsistent Values
    df['category_col'] = ['Apple'] * 40 + ['apple'] * 5 + ['Orange'] * 40 + ['orange '] * 5 + ['Banana'] * 10
    
    print("Analyzing...")
    analyzer = pdq.analyze_dataframe(df)
    
    print("\nInspecting Issues directly:")
    found_details = False
    for issue in analyzer.issues:
        print(f"Column: {issue.column}, Type: {issue.issue_type}")
        print(f"Details: {issue.details}")
        
        if 'outlier_examples' in issue.details or 'examples' in issue.details:
            found_details = True
            print("  -> FOUND EXAMPLES!")
            
    if not found_details:
        print("\n[FAIL] No examples found in details!")
        sys.exit(1)
        
    print("\nGenerating Report...")
    report_path = "debug_details_report.html"
    pdq.generate_report(analyzer, output_path=report_path, format='html')
    print(f"Report saved to {report_path}. Please open it and check the 'Details' column.")

if __name__ == "__main__":
    debug_details()
