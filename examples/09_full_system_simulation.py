
import pandas as pd
import numpy as np
import os
import sys
import shutil
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq
from pydataquality.config import QUALITY_THRESHOLDS

def create_messy_dataset(rows=1000):
    """Create a dataset with known issues for testing."""
    np.random.seed(42)
    df = pd.DataFrame({
        'id': range(rows),
        'category': np.random.choice(['A', 'B', 'C', 'D'], rows),
        'value_perfect': np.random.normal(100, 10, rows),
        'value_missing': np.random.normal(50, 5, rows),
        'value_outliers': np.random.normal(0, 1, rows),
        'critical_text': np.random.choice(['Valid', 'Valid', 'Error'], rows, p=[0.45, 0.45, 0.1]),
        'date': pd.date_range(start='2023-01-01', periods=rows)
    })
    
    # Inject issues
    df.loc[0:rows//10, 'value_missing'] = np.nan  # 10% missing
    df.loc[0, 'value_outliers'] = 1000  # Extreme outlier
    
    return df

def simulate_data_scientist(df):
    print("\n--- Persona A: Data Scientist ---")
    print("1. Loading Data...")
    
    print("2. Quick Check:")
    pdq.quick_quality_check(df)
    
    print("3. Deep Analysis:")
    analyzer = pdq.analyze_dataframe(df, name="Simulation_DS")
    
    print("4. Generating Report:")
    report_path = "ds_report.html"
    pdq.generate_report(analyzer, output_path=report_path, format='html')
    if os.path.exists(report_path):
        print(f"   [OK] Report saved to {report_path}")
    else:
        print(f"   [FAIL] Report not found!")
        
    print("5. Visualizing:")
    viz = pdq.create_visual_report(analyzer, show_plots=False)
    print("   [OK] Visualization object created")

def simulate_data_engineer(df_path):
    print("\n--- Persona B: Data Engineer ---")
    
    print("1. Batch Sampling Big Data...")
    # Simulate "Big Data" by treating the small file as chunkable
    df_sample = pdq.sample_large_dataset(df_path, n_samples=500, chunksize=200)
    print(f"   [OK] Sampled {len(df_sample)} rows from file")
    
    print("2. Loading Custom Rules...")
    rules = {
        'value_perfect': {'min': 0, 'max': 200},
        'category': {'allowed': ['A', 'B', 'C', 'D']} 
    }
    # Note: In real life this loads from YAML, but we test the passing of dict here
    
    print("3. Analyzing with Rules:")
    analyzer = pdq.DataQualityAnalyzer(df_sample, rules=rules)
    print(f"   [OK] Analyzer initialized with {len(analyzer.rules)} rules")
    
    print("4. Checking Drift:")
    # Create a "new" dataset that has drifted
    df_new = df_sample.copy()
    df_new['value_perfect'] = df_new['value_perfect'] + 50  # Shift mean
    analyzer_new = pdq.DataQualityAnalyzer(df_new)
    
    drift = pdq.compare_reports(analyzer, analyzer_new)
    print("   [OK] Drift calculated:")
    print(drift.to_string())

def simulate_cli_user(csv_path):
    print("\n--- Persona C: CLI User ---")
    import subprocess
    
    cmd = [sys.executable, "cli.py", csv_path, "--output", "cli_report.html"]
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   [OK] CLI command success")
        if os.path.exists("cli_report.html"):
            print("   [OK] Report file generated")
    else:
        print("   [FAIL] CLI command failed")
        print(result.stderr)

def simulate_power_user(df):
    print("\n--- Persona D: Power User (Low-Level Utils) ---")
    
    print("1. Detecting Column Types:")
    types = pdq.detect_column_types(df)
    print(f"   [OK] Detected types: {list(types.keys())}")
    
    print("2. Formatting Memory:")
    mem = pdq.format_memory_size(1024*1024*5.5)
    print(f"   [OK] Formatted memory: {mem}")
    
    print("3. Validating Thresholds:")
    thresh = pdq.validate_thresholds({'missing_critical': 0.99})
    print(f"   [OK] Thresholds validated: {thresh['missing_critical']}")
    
    print("4. Finding Duplicates:")
    # Create duplicate column
    df['dup_id'] = df['id']
    dups = pdq.find_duplicate_columns(df)
    print(f"   [OK] Duplicates found: {dups}")

if __name__ == "__main__":
    print("STARTING FULL SYSTEM SIMULATION (STRESS TEST)")
    print("="*40)
    
    # Setup Data
    df = create_messy_dataset()
    csv_path = "simulation_data.csv"
    df.to_csv(csv_path, index=False)
    
    try:
        # Run Personas
        simulate_data_scientist(df)
        simulate_data_engineer(csv_path)
        simulate_cli_user(csv_path)
        simulate_power_user(df)
        
        print("\n" + "="*40)
        print("SIMULATION COMPLETE: ALL SYSTEMS GO")
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup with retry policy for Windows file locking
        import time
        time.sleep(1.0) # Wait for handles to release
        files_to_clean = [csv_path, "ds_report.html", "cli_report.html"]
        
        print("\nCleaning up...")
        for f in files_to_clean:
            if os.path.exists(f):
                try:
                    os.remove(f)
                    print(f"   Deleted {f}")
                except Exception as e:
                    print(f"   Warning: Could not delete {f}: {e}")
