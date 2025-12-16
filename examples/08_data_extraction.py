"""
Example 08: Data Extraction and Remediation
Demonstrates extracting problematic rows for fixing.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def main():
    print("Data Extraction Example")
    print("="*60)
    
    # Create sample data with issues
    np.random.seed(42)
    df = pd.DataFrame({
        'customer_id': range(1, 101),
        'age': np.concatenate([np.random.randint(18, 70, 95), [150, 200, 5, np.nan, np.nan]]),
        'income': np.concatenate([np.random.randint(20000, 150000, 97), [np.nan, np.nan, 500000]]),
        'city': np.random.choice(['NYC', 'LA', 'Chicago', 'Houston'], 100)
    })
    
    # Analyze
    print("\nAnalyzing data...")
    analyzer = pdq.analyze_dataframe(df, name="Customer Data")
    
    print(f"Found {len(analyzer.issues)} quality issues")
    
    # Extract problematic rows for 'age'
    print("\nExtracting problematic age values...")
    bad_ages = analyzer.get_problematic_rows('age', issue_type='all')
    
    print(f"Found {len(bad_ages)} rows with age issues:")
    print(bad_ages[['customer_id', 'age', 'income']])
    
    # Extract only outliers
    print("\nExtracting only outliers in 'income'...")
    income_outliers = analyzer.get_problematic_rows('income', issue_type='outliers')
    
    print(f"Found {len(income_outliers)} income outliers:")
    print(income_outliers[['customer_id', 'age', 'income']])
    
    # Save for manual review
    bad_ages.to_csv('ages_to_fix.csv', index=False)
    print("\nSaved problematic rows to: ages_to_fix.csv")
    
    print("\nYou can now:")
    print("1. Review ages_to_fix.csv")
    print("2. Fix the issues manually or programmatically")
    print("3. Re-run the analysis")
    
    # Cleanup
    os.remove('ages_to_fix.csv')
    
    print("\n" + "="*60)
    print("Example complete!")

if __name__ == "__main__":
    main()
