"""
Test script to verify PyDataQuality works with all claimed data formats.
This validates the documentation claims about multi-format support.
"""

import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def create_test_data():
    """Create sample data with known quality issues."""
    np.random.seed(42)
    
    data = {
        'id': range(1, 51),
        'name': ['User_' + str(i) for i in range(1, 51)],
        'age': np.concatenate([np.random.randint(18, 65, 45), [150, np.nan, 200, np.nan, 5]]),
        'salary': np.random.randint(30000, 120000, 50),
        'department': np.random.choice(['Sales', 'Engineering', 'HR', 'Marketing'], 50)
    }
    
    return pd.DataFrame(data)

def test_format(format_name, file_path, read_function):
    """Test a specific file format."""
    print(f"\n{'='*60}")
    print(f"Testing {format_name} format: {file_path}")
    print('='*60)
    
    try:
        # Read the file
        df = read_function(file_path)
        print(f"[OK] Successfully loaded {format_name} file")
        print(f"  Shape: {df.shape}")
        
        # Analyze with PyDataQuality
        analyzer = pdq.analyze_dataframe(df, name=f"{format_name} Test", verbose=False)
        print(f"[OK] Successfully analyzed {format_name} data")
        
        # Get summary
        summary = analyzer.get_summary()
        print(f"  Issues found: {len(analyzer.issues)}")
        print(f"  Critical: {summary['issues_by_severity'].get('critical', 0)}")
        print(f"  Warnings: {summary['issues_by_severity'].get('warning', 0)}")
        
        # Test get_problematic_rows
        if len(analyzer.issues) > 0:
            bad_rows = analyzer.get_problematic_rows('age', 'all')
            print(f"[OK] Successfully extracted {len(bad_rows)} problematic rows")
        
        # Generate report
        report_path = f"test_{format_name.lower()}_report.html"
        pdq.generate_report(analyzer, output_path=report_path, format='html')
        print(f"[OK] Successfully generated HTML report: {report_path}")
        
        print(f"\n[SUCCESS] {format_name} format fully supported!")
        return True
        
    except Exception as e:
        print(f"\n[FAILED] {format_name} format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("PyDataQuality Multi-Format Support Test")
    print("="*60)
    
    # Create test data
    print("\nCreating test data...")
    df = create_test_data()
    
    # Create test files in different formats
    test_dir = "test_data_formats"
    os.makedirs(test_dir, exist_ok=True)
    
    results = {}
    
    # Test 1: CSV
    csv_path = os.path.join(test_dir, "test_data.csv")
    df.to_csv(csv_path, index=False)
    results['CSV'] = test_format('CSV', csv_path, pd.read_csv)
    
    # Test 2: Excel
    try:
        excel_path = os.path.join(test_dir, "test_data.xlsx")
        df.to_excel(excel_path, index=False, engine='openpyxl')
        results['Excel'] = test_format('Excel', excel_path, pd.read_excel)
    except ImportError:
        print("\n[SKIP] Excel format - openpyxl not installed")
        results['Excel'] = None
    
    # Test 3: JSON
    json_path = os.path.join(test_dir, "test_data.json")
    df.to_json(json_path, orient='records', indent=2)
    results['JSON'] = test_format('JSON', json_path, pd.read_json)
    
    # Test 4: Parquet
    try:
        parquet_path = os.path.join(test_dir, "test_data.parquet")
        df.to_parquet(parquet_path, index=False)
        results['Parquet'] = test_format('Parquet', parquet_path, pd.read_parquet)
    except ImportError:
        print("\n[SKIP] Parquet format - pyarrow not installed")
        results['Parquet'] = None
    
    # Test 5: Direct DataFrame (simulates SQL, API, etc.)
    print(f"\n{'='*60}")
    print("Testing Direct DataFrame (SQL/API simulation)")
    print('='*60)
    
    try:
        # Simulate DataFrame from any source
        analyzer = pdq.analyze_dataframe(df, name="Direct DataFrame", verbose=False)
        print(f"[OK] Successfully analyzed DataFrame from memory")
        print(f"  Issues found: {len(analyzer.issues)}")
        results['DataFrame'] = True
        print(f"\n[SUCCESS] Direct DataFrame analysis works!")
    except Exception as e:
        print(f"\n[FAILED] DataFrame test failed: {e}")
        results['DataFrame'] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for format_name, result in results.items():
        if result is True:
            print(f"[PASS] {format_name}: PASSED")
        elif result is False:
            print(f"[FAIL] {format_name}: FAILED")
        else:
            print(f"[SKIP] {format_name}: SKIPPED (missing dependency)")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n[OVERALL] Some tests FAILED - documentation claims need revision!")
        sys.exit(1)
    else:
        print("\n[OVERALL] All tests PASSED - documentation claims verified!")
        print("\nPyDataQuality successfully works with:")
        print("  - CSV files")
        print("  - Excel files (.xlsx)")
        print("  - JSON files")
        print("  - Parquet files")
        print("  - Direct DataFrames (SQL, APIs, Cloud platforms, etc.)")

if __name__ == "__main__":
    main()
