
import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def verify_extraction():
    print("Verifying get_problematic_rows()...")
    
    df = pd.DataFrame({
        'id': range(10),
        'value': [1, 2, 3, 4, 5, 1000, 7, 8, np.nan, 10]
    })
    
    analyzer = pdq.analyze_dataframe(df)
    
    # Test 1: Get Outliers
    print("\n1. Testing Outlier Extraction...")
    outliers = analyzer.get_problematic_rows('value', issue_type='outliers')
    print(f"   Found {len(outliers)} outliers")
    print(outliers)
    
    if len(outliers) == 1 and outliers.iloc[0]['value'] == 1000:
        print("   [OK] Correctly identified outlier 1000")
    else:
        print("   [FAIL] Outlier extraction failed")
        
    # Test 2: Get Missing
    print("\n2. Testing Missing Value Extraction...")
    missing = analyzer.get_problematic_rows('value', issue_type='missing_values')
    print(f"   Found {len(missing)} missing rows")
    print(missing)
    
    if len(missing) == 1 and pd.isna(missing.iloc[0]['value']):
        print("   [OK] Correctly identified missing value")
    else:
        print("   [FAIL] Missing extraction failed")
        
    # Test 3: Get All
    print("\n3. Testing All Issues...")
    all_bad = analyzer.get_problematic_rows('value', issue_type='all')
    if len(all_bad) == 2:
        print("   [OK] Found both issues")
    else:
        print(f"   [FAIL] Expected 2 rows, got {len(all_bad)}")

if __name__ == "__main__":
    verify_extraction()
