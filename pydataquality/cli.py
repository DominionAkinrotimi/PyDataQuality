#!/usr/bin/env python3
"""
Command-line interface for PyDataQuality.
"""

import argparse
import sys
import os
import pandas as pd

# Use relative imports for package compatibility
try:
    from . import (
        analyze_dataframe,
        generate_report,
        sample_dataframe,
        create_visual_report,
        load_rules_from_yaml,
    )
except ImportError:
    # Fallback if run as script directly (not recommended for package usage)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pydataquality import (
        analyze_dataframe,
        generate_report,
        sample_dataframe,
        create_visual_report,
        load_rules_from_yaml,
    )

EXTENSION_FORMATS = {
    ".csv": "csv",
    ".tsv": "csv",
    ".txt": "csv",
    ".xlsx": "excel",
    ".xls": "excel",
    ".json": "json",
    ".parquet": "parquet",
}


def load_data(path, file_format="auto"):
    """Load a data file. ``file_format='auto'`` picks the reader from the extension."""
    if file_format == "auto":
        ext = os.path.splitext(path)[1].lower()
        file_format = EXTENSION_FORMATS.get(ext)
        if file_format is None:
            print(f"Warning: Unknown extension '{ext}', trying CSV...")
            file_format = "csv"

    if file_format == "csv":
        sep = "\t" if path.lower().endswith(".tsv") else ","
        return pd.read_csv(path, sep=sep)
    if file_format == "excel":
        return pd.read_excel(path)
    if file_format == "json":
        return pd.read_json(path)
    if file_format == "parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported format: {file_format}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="PyDataQuality - Automated Data Quality Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.csv                          # Quick quality check
  %(prog)s data.csv --report html --theme professional  # Professional report
  %(prog)s data.csv --visualize              # Create visualizations
  %(prog)s data.csv --output results/        # Save all outputs to directory
  %(prog)s data.csv --rules rules.yaml --fail-on critical  # Gate a pipeline
        """,
    )

    parser.add_argument(
        "file", help="Input data file (CSV, Excel, JSON, or Parquet)"
    )
    parser.add_argument("--name", default="Dataset", help="Name of the dataset")
    parser.add_argument(
        "--format",
        choices=["auto", "csv", "excel", "json", "parquet"],
        default="auto",
        help="Input file format (default: detect from the file extension)",
    )
    parser.add_argument(
        "--report",
        choices=["html", "text", "json", "none"],
        default="html",
        help="Report format (default: html)",
    )
    parser.add_argument(
        "--theme",
        choices=["creative", "professional", "simple"],
        default="creative",
        help="Report theme (HTML only)",
    )
    parser.add_argument(
        "--output", help="Output directory for reports and visualizations"
    )
    parser.add_argument(
        "--visualize", action="store_true", help="Create and save visualizations"
    )
    parser.add_argument("--sample", type=int, help="Sample size for large datasets")
    parser.add_argument("--rules", help="YAML file with custom validation rules")
    parser.add_argument(
        "--fail-on",
        choices=["never", "critical", "warning"],
        default="never",
        help="Exit with code 2 when issues of this severity (or worse) are found. "
        "Use it to stop a pipeline or CI job on bad data (default: never)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Display detailed progress information"
    )

    args = parser.parse_args(argv)

    try:
        df = load_data(args.file, args.format)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)

    print(f"Loaded {args.file}: {df.shape[0]} rows, {df.shape[1]} columns")

    # Sample if requested
    if args.sample and args.sample < len(df):
        df = sample_dataframe(df, n_samples=args.sample)
        print(f"Sampled to: {len(df)} rows")

    output_path = args.output or "."
    if args.output:
        os.makedirs(args.output, exist_ok=True)

    rules = load_rules_from_yaml(args.rules) if args.rules else None

    # Perform analysis
    analyzer = analyze_dataframe(
        df, name=args.name, verbose=args.verbose, rules=rules
    )

    # Generate report
    if args.report != "none":
        extension = "txt" if args.report == "text" else args.report
        report_file = os.path.join(
            output_path,
            f"{args.name.replace(' ', '_')}_quality_report.{extension}",
        )

        # Pass theme only if format is html
        kwargs = {}
        if args.report == "html":
            kwargs["theme"] = args.theme

        generate_report(analyzer, output_path=report_file, format=args.report, **kwargs)
        print(f"Report saved to: {report_file}")

    # Create visualizations
    if args.visualize:
        viz_dir = os.path.join(output_path, "visualizations")
        create_visual_report(analyzer, save_path=viz_dir, show_plots=False)
        print(f"Visualizations saved to: {viz_dir}")

    # Display quick summary
    summary = analyzer.get_summary()
    critical = summary["issues_by_severity"].get("critical", 0)
    warning = summary["issues_by_severity"].get("warning", 0)
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Critical issues: {critical}")
    print(f"Warning issues: {warning}")
    if "missing_data_overview" in summary:
        print(
            f"Total missing: {summary['missing_data_overview']['total_missing_cells']:,} "
            f"({summary['missing_data_overview']['total_missing_percentage']:.1f}%)"
        )
    print("=" * 60)

    if args.verbose:
        for issue in analyzer.issues:
            print(f"[{issue.severity}] {issue.column}: {issue.message}")

    failed = (args.fail_on == "critical" and critical > 0) or (
        args.fail_on == "warning" and (critical > 0 or warning > 0)
    )
    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
