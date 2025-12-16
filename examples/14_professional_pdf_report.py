"""
Generate a professional PDF-optimized report.
This demonstrates the 'professional' theme for clean PDF exports.
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def create_demo_data():
    """Create sample data with various quality issues."""
    np.random.seed(42)
    
    data = {
        'customer_id': range(1, 101),
        'name': [f'Customer_{i}' for i in range(1, 101)],
        'age': np.concatenate([
            np.random.randint(18, 70, 90),
            [150, 200, 5, np.nan, np.nan, 180, 190, 3, np.nan, 175]
        ]),
        'salary': np.concatenate([
            np.random.randint(30000, 150000, 95),
            [500000, 600000, 10000, np.nan, 450000]
        ]),
        'department': np.random.choice(['Sales', 'Engineering', 'HR', 'Marketing', 'Finance'], 100),
        'join_date': pd.date_range('2020-01-01', periods=100, freq='3D'),
        'email': [f'user{i}@company.com' if i % 10 != 0 else np.nan for i in range(1, 101)]
    }
    
    return pd.DataFrame(data)

def main():
    print("Generating Professional PDF-Optimized Report...")
    
    # Create sample data
    df = create_demo_data()
    
    # Analyze
    print("Analyzing data...")
    analyzer = pdq.analyze_dataframe(df, name="Professional Report Demo", verbose=False)
    
    print(f"Found {len(analyzer.issues)} quality issues")
    
    # Generate PROFESSIONAL theme report (PDF-optimized)
    output_path = "professional_pdf_report.html"
    pdq.generate_report(analyzer, output_path=output_path, format='html', theme='professional')
    
    print(f"\n{'='*60}")
    print("PROFESSIONAL PDF REPORT GENERATED")
    print('='*60)
    print(f"\nReport: {output_path}")
    print("\nTheme: PROFESSIONAL (Clean, PDF-optimized)")
    print("\nFeatures:")
    print("  - Clean white background")
    print("  - Professional typography")
    print("  - Print-optimized layout")
    print("  - Perfect for PDF export (Ctrl+P -> Save as PDF)")
    
    print(f"\n{'='*60}")
    print("Opening report in browser...")
    print('='*60)
    
    # Open in browser
    os.system(f'start {output_path}')

if __name__ == "__main__":
    main()
