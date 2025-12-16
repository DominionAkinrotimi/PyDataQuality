"""
Example 05: Interactive Notebook Usage
Demonstrates using PyDataQuality in Jupyter/Colab notebooks.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def main():
    print("Interactive Notebook Example")
    print("="*60)
    
    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        'user_id': range(1, 101),
        'age': np.concatenate([np.random.randint(18, 70, 95), [150, 200, 5, np.nan, np.nan]]),
        'score': np.random.uniform(0, 100, 100),
        'status': np.random.choice(['Active', 'Inactive', 'Pending'], 100)
    })
    
    # Analyze
    print("\nAnalyzing data...")
    analyzer = pdq.analyze_dataframe(df, name="User Data")
    
    # In a Jupyter notebook, you would use:
    # pdq.show_report(analyzer, theme='creative')
    
    # For this example, we'll generate an HTML file
    print("\nGenerating interactive report...")
    pdq.generate_report(analyzer, output_path="interactive_report.html", 
                       format='html', theme='creative')
    
    print("\nReport generated: interactive_report.html")
    print("\nIn Jupyter/Colab, use:")
    print("  pdq.show_report(analyzer, theme='creative')")
    print("\nThis will display the report directly in the notebook!")
    
    print("\n" + "="*60)
    print("Example complete!")

if __name__ == "__main__":
    main()
