"""
Example 04: PDF Report Generation
Demonstrates how to generate professional PDF-ready reports.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def main():
    print("PDF Report Example")
    print("="*60)
    
    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        'product_id': range(1, 51),
        'product_name': [f'Product_{i}' for i in range(1, 51)],
        'price': np.random.uniform(10, 1000, 50),
        'stock': np.random.randint(0, 100, 50),
        'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books'], 50)
    })
    
    # Analyze
    analyzer = pdq.analyze_dataframe(df, name="Product Inventory")
    
    # Generate professional PDF-ready report
    print("\nGenerating PDF-ready report...")
    pdq.generate_report(analyzer, output_path="product_report.html", 
                       format='html', theme='professional')
    
    print("\nReport generated: product_report.html")
    print("\nTo export as PDF:")
    print("1. Open product_report.html in your browser")
    print("2. Press Ctrl+P (Windows) or Cmd+P (Mac)")
    print("3. Select 'Save as PDF'")
    print("4. Save the file")
    
    print("\n" + "="*60)
    print("Example complete!")

if __name__ == "__main__":
    main()
