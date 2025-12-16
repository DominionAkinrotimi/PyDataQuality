# cli.py
#!/usr/bin/env python3
"""
Command-line interface for PyDataQuality.
"""

import argparse
import sys
import os
import pandas as pd

# Add current directory to path for development
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pydataquality as pdq


def main():
    parser = argparse.ArgumentParser(
        description='PyDataQuality - Automated Data Quality Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.csv                          # Quick quality check
  %(prog)s data.csv --name "Sales Data"      # Name the dataset
  %(prog)s data.csv --report html            # Generate HTML report
  %(prog)s data.csv --visualize              # Create visualizations
  %(prog)s data.csv --output results/        # Save all outputs to directory
        """
    )
    
    parser.add_argument('file', help='Input data file (CSV, Excel, or JSON)')
    parser.add_argument('--name', default='Dataset', help='Name of the dataset')
    parser.add_argument('--format', choices=['csv', 'excel', 'json'], 
                       default='csv', help='Input file format')
    parser.add_argument('--report', choices=['html', 'text', 'json', 'none'], 
                       default='html', help='Report format (default: html)')
    parser.add_argument('--output', help='Output directory for reports and visualizations')
    parser.add_argument('--visualize', action='store_true', 
                       help='Create and save visualizations')
    parser.add_argument('--sample', type=int, 
                       help='Sample size for large datasets')
    parser.add_argument('--verbose', action='store_true', 
                       help='Display detailed progress information')
    
    args = parser.parse_args()
    
    # 1. Determine file type
    ext = os.path.splitext(args.file)[1].lower()
    
    # 2. Load Data
    try:
        if ext == '.csv':
            df = pd.read_csv(args.file)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(args.file)
        elif ext == '.json':
            df = pd.read_json(args.file)
        elif ext == '.parquet':
            df = pd.read_parquet(args.file)
        else:
            # Fallback to user provided format or CSV
            print(f"Warning: Unknown extension '{ext}', trying CSV...")
            df = pd.read_csv(args.file)
            
        print(f"Successfully loaded {args.file} with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)
    
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Sample if requested
    if args.sample and args.sample < len(df):
        df = pdq.sample_dataframe(df, n_samples=args.sample)
        print(f"Sampled to: {len(df)} rows")
    
    # Create output directory if specified
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        output_path = args.output
    else:
        output_path = '.'
    
    # Perform analysis
    analyzer = pdq.analyze_dataframe(df, name=args.name, verbose=args.verbose)
    
    # Generate report
    if args.report != 'none':
        report_file = os.path.join(output_path, f"{args.name.replace(' ', '_')}_quality_report.{args.report}")
        pdq.generate_report(analyzer, output_path=report_file, format=args.report)
        print(f"Report saved to: {report_file}")
    
    # Create visualizations
    if args.visualize:
        viz_dir = os.path.join(output_path, 'visualizations')
        visualizer = pdq.create_visual_report(analyzer, save_dir=viz_dir, show_plots=False)
        print(f"Visualizations saved to: {viz_dir}")
    
    # Display quick summary
    summary = analyzer.get_summary()
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Critical issues: {summary['issues_by_severity'].get('critical', 0)}")
    print(f"Warning issues: {summary['issues_by_severity'].get('warning', 0)}")
    print(f"Total missing: {summary['missing_data_overview']['total_missing_cells']:,} "
          f"({summary['missing_data_overview']['total_missing_percentage']:.1f}%)")
    print("=" * 60)


if __name__ == '__main__':
    main()