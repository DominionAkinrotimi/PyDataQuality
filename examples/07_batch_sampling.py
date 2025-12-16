"""
Example 07: Batch Sampling for Large Datasets
Demonstrates efficient sampling from large CSV files.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def main():
    print("Batch Sampling Example")
    print("="*60)
    
    # Create a large sample CSV file
    print("\nCreating large sample CSV file...")
    large_df = pd.DataFrame({
        'id': range(1, 100001),
        'value': np.random.randn(100000),
        'category': np.random.choice(['A', 'B', 'C', 'D'], 100000),
        'timestamp': pd.date_range('2020-01-01', periods=100000, freq='1min')
    })
    
    large_df.to_csv('large_dataset.csv', index=False)
    print("Created large_dataset.csv (100,000 rows)")
    
    # Sample efficiently without loading entire file
    print("\nSampling 5,000 rows efficiently...")
    sampled_df = pdq.sample_large_dataset('large_dataset.csv', n_samples=5000)
    
    print(f"Sampled {len(sampled_df)} rows from 100,000 total")
    
    # Analyze the sample
    print("\nAnalyzing sampled data...")
    analyzer = pdq.analyze_dataframe(sampled_df, name="Large Dataset Sample")
    
    # Generate report
    pdq.generate_report(analyzer, output_path="large_dataset_report.html")
    
    print("\nReport generated: large_dataset_report.html")
    print(f"Memory saved by sampling: ~{(100000-5000)/100000*100:.0f}%")
    
    # Cleanup
    os.remove('large_dataset.csv')
    
    print("\n" + "="*60)
    print("Example complete!")

if __name__ == "__main__":
    main()
