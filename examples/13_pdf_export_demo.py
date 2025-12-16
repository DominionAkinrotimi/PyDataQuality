"""
Generate a sample report to demonstrate PDF export capability.
This shows the "Save as PDF" feature via browser print.
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def create_demo_data():
    """Create sample data with various quality issues for demonstration."""
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
    print("Generating PDF-ready report demonstration...")
    
    # Create sample data
    df = create_demo_data()
    
    # Analyze
    print("Analyzing data...")
    analyzer = pdq.analyze_dataframe(df, name="PDF Export Demo", verbose=False)
    
    print(f"Found {len(analyzer.issues)} quality issues")
    
    # Generate HTML report (optimized for PDF export)
    output_path = "pdf_export_demo_report.html"
    pdq.generate_report(analyzer, output_path=output_path, format='html')
    
    print(f"\n{'='*60}")
    print("PDF EXPORT DEMONSTRATION")
    print('='*60)
    print(f"\nReport generated: {output_path}")
    print("\nTo export as PDF:")
    print("1. Open the HTML file in your browser")
    print("2. Press Ctrl+P (Windows) or Cmd+P (Mac)")
    print("3. Select 'Save as PDF' as the destination")
    print("4. Click 'Save'")
    print("\nThe report includes:")
    print("  - Print-optimized CSS for clean PDF output")
    print("  - Dark theme with professional styling")
    print("  - All quality issues with details")
    print("  - AI remediation prompts")
    print("  - Summary statistics")
    
    print(f"\n{'='*60}")
    print("Report ready for PDF export!")
    print('='*60)

if __name__ == "__main__":
    main()
