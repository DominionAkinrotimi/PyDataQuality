"""
Report generation module for data quality analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import json
from jinja2 import Environment

from .analyzer import DataQualityAnalyzer
from .config import REPORT_CONFIG


class QualityReportGenerator:
    """
    Generate comprehensive reports from data quality analysis.
    """
    
    def __init__(self, analyzer: DataQualityAnalyzer):
        self.analyzer = analyzer

    def generate_ai_remediation_prompt(self, include_eda: bool = True) -> str:
        """
        Generate an AI remediation prompt for fixing data quality issues.
        
        This creates a prompt that can be copied to an AI assistant to get
        automated code for fixing the detected quality issues.
        
        Parameters
        ----------
        include_eda : bool
            Whether to include statistical context (EDA) in the prompt.
        
        Returns
        -------
        str
            AI remediation prompt text
        """
        summary = self.analyzer.get_summary()
        
        prompt = f"I have a dataset '{self.analyzer.name}' with {summary['dataset']['rows']} rows. "
        
        # Get critical and warning issues with DETAILS
        significant_issues = []
        affected_columns = set()
        
        for issue in self.analyzer.issues:
            if issue.severity in ['critical', 'warning']:
                affected_columns.add(issue.column)
                # Basic description
                desc = f"{issue.column} ({issue.issue_type}"
                
                # Add context based on details
                details = []
                if issue.issue_type == 'outliers' and issue.details:
                    lower = issue.details.get('lower_bound')
                    upper = issue.details.get('upper_bound')
                    if lower is not None and upper is not None:
                        details.append(f"outside [{lower:.2f}, {upper:.2f}]")
                        
                elif issue.issue_type == 'missing_values':
                    details.append(f"{issue.affected_percentage:.1f}% missing")
                    
                elif issue.issue_type == 'inconsistent_values' and issue.details:
                    examples = issue.details.get('examples', [])
                    if examples:
                        details.append(f"e.g., {', '.join(examples[:3])}")
                
                # Close description
                if details:
                    desc += f": {'; '.join(details)})"
                else:
                    desc += ")"
                
                significant_issues.append(desc)
        
        if significant_issues:
            prompt += f"It has the following quality issues: {', '.join(significant_issues)}. "
            
            # Inject EDA Context if requested
            if include_eda and affected_columns:
                prompt += "\n\nHere is the statistical context (EDA) for the affected columns:\n"
                for col in affected_columns:
                    if col in self.analyzer.column_stats:
                        stats = self.analyzer.column_stats[col]
                        prompt += f"- {col} ({stats.dtype}): "
                        
                        # Add specific stats based on type
                        context = []
                        if 'mean' in stats.stats:
                            context.append(f"Mean={stats.stats['mean']:.2f}")
                            context.append(f"Median={stats.stats.get('median', 0):.2f}")
                            context.append(f"Min={stats.stats.get('min', 0):.2f}")
                            context.append(f"Max={stats.stats.get('max', 0):.2f}")
                        else:
                            # Categorical / Object stats
                            context.append(f"Unique Values={stats.unique_count}")
                            if 'most_common' in stats.stats:
                                context.append(f"Top Value='{stats.stats['most_common']}'")
                                
                        prompt += ", ".join(context) + "\n"
            
            prompt += "\nPlease write a Python script using pandas to clean this dataset. "
            prompt += "Consider different strategies (e.g., capping vs removal for outliers, imputation vs dropping for missing) "
            prompt += "based on the logic and EDA context provided above. Provide a brief explanation of your chosen strategy."
        else:
            prompt += "The data quality appears good, but I'd like to optimize it further. Please suggest improvements."
        
        return prompt
       
    def generate_text_report(self) -> str:
        """
        Generate a detailed text report.
        
        Returns
        -------
        str
            Formatted text report
        """
        summary = self.analyzer.get_summary()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"DATA QUALITY ANALYSIS REPORT")
        report_lines.append(f"Dataset: {self.analyzer.name}")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        
        # Dataset Overview
        report_lines.append("\nDATASET OVERVIEW")
        report_lines.append("-" * 40)
        report_lines.append(f"Rows: {summary['dataset']['rows']:,}")
        report_lines.append(f"Columns: {summary['columns']:,}")
        report_lines.append(f"Total Cells: {summary['dataset']['total_cells']:,}")
        report_lines.append(f"Memory Usage: {summary['dataset']['memory_usage_mb']:.2f} MB")
        
        # Column Types Summary
        report_lines.append("\nCOLUMN TYPES")
        report_lines.append("-" * 40)
        for dtype, count in summary['column_types'].items():
            report_lines.append(f"{dtype.title()}: {count}")
        
        # Issues Summary
        report_lines.append("\nISSUES SUMMARY")
        report_lines.append("-" * 40)
        severity_counts = summary['issues_by_severity']
        report_lines.append(f"Critical Issues: {severity_counts.get('critical', 0)}")
        report_lines.append(f"Warning Issues: {severity_counts.get('warning', 0)}")
        report_lines.append(f"Informational Issues: {severity_counts.get('info', 0)}")
        
        if severity_counts.get('critical', 0) + severity_counts.get('warning', 0) > 0:
            report_lines.append("\nDETAILED ISSUES")
            report_lines.append("-" * 40)
            
            # Group issues by column
            issues_by_column = {}
            for issue in self.analyzer.issues:
                if issue.severity in ['critical', 'warning']:
                    if issue.column not in issues_by_column:
                        issues_by_column[issue.column] = []
                    issues_by_column[issue.column].append(issue)
            
            for column, issues in issues_by_column.items():
                report_lines.append(f"\n{column}:")
                for issue in issues:
                    report_lines.append(f"  [{issue.severity.upper()}] {issue.issue_type}")
                    report_lines.append(f"      {issue.message}")
                    if issue.affected_count > 0:
                        report_lines.append(f"      Affected: {issue.affected_count} ({issue.affected_percentage:.1f}%)")
                    # Show details if available
                    if issue.details:
                        if 'examples' in issue.details:
                            report_lines.append(f"      Examples: {', '.join(issue.details['examples'][:3])}")
                        if 'outlier_examples' in issue.details:
                            examples = [str(x) for x in issue.details['outlier_examples']]
                            report_lines.append(f"      Outlier examples: {', '.join(examples)}")
        
        # Missing Data Overview
        report_lines.append("\nMISSING DATA OVERVIEW")
        report_lines.append("-" * 40)
        missing_overview = summary['missing_data_overview']
        report_lines.append(f"Columns with missing values: {missing_overview['columns_with_missing']}")
        report_lines.append(f"Total missing cells: {missing_overview['total_missing_cells']:,}")
        report_lines.append(f"Overall missing percentage: {missing_overview['total_missing_percentage']:.2f}%")
        
        if missing_overview['columns']:
            report_lines.append("\nTop columns with missing values:")
            for col_data in missing_overview['columns']:
                report_lines.append(f"  {col_data['column']}: {col_data['missing_count']:,} ({col_data['missing_percentage']:.1f}%)")
        
        # Column Statistics Summary
        report_lines.append("\nCOLUMN STATISTICS SUMMARY")
        report_lines.append("-" * 40)
        
        numeric_cols = [col for col, stats in self.analyzer.column_stats.items() 
                       if 'mean' in stats.stats]
        
        if numeric_cols:
            report_lines.append("\nNumeric Columns:")
            for col in numeric_cols[:5]:  # Show first 5
                stats = self.analyzer.column_stats[col]
                report_lines.append(f"\n  {col}:")
                report_lines.append(f"    Type: {stats.dtype}")
                report_lines.append(f"    Missing: {stats.missing_percentage:.1f}%")
                report_lines.append(f"    Mean: {stats.stats.get('mean', 0):.4f}")
                report_lines.append(f"    Std: {stats.stats.get('std', 0):.4f}")
                report_lines.append(f"    Range: [{stats.stats.get('min', 0):.4f}, {stats.stats.get('max', 0):.4f}]")
            
            if len(numeric_cols) > 5:
                report_lines.append(f"\n  ... and {len(numeric_cols) - 5} more numeric columns")
        
        categorical_cols = [col for col, stats in self.analyzer.column_stats.items() 
                          if 'value_counts' in stats.stats]
        
        if categorical_cols:
            report_lines.append("\nCategorical Columns:")
            for col in categorical_cols[:3]:  # Show first 3
                stats = self.analyzer.column_stats[col]
                report_lines.append(f"\n  {col}:")
                report_lines.append(f"    Type: {stats.dtype}")
                report_lines.append(f"    Missing: {stats.missing_percentage:.1f}%")
                report_lines.append(f"    Unique values: {stats.unique_count}")
                if 'most_common' in stats.stats:
                    report_lines.append(f"    Most common: '{stats.stats['most_common']}' ({stats.stats['most_common_percentage']:.1f}%)")
            
            if len(categorical_cols) > 3:
                report_lines.append(f"\n  ... and {len(categorical_cols) - 3} more categorical columns")
        
        # Recommendations
        report_lines.append("\nRECOMMENDATIONS")
        report_lines.append("-" * 40)
        
        recommendations = []
        
        # Check for critical issues
        if severity_counts.get('critical', 0) > 0:
            recommendations.append("Address critical issues before proceeding with analysis.")
        
        # Check for high missing values
        if missing_overview['total_missing_percentage'] > 20:
            recommendations.append("Consider data imputation or investigate sources of missing data.")
        elif missing_overview['total_missing_percentage'] > 5:
            recommendations.append("Review missing data patterns and consider appropriate handling methods.")
        
        # Check for skewed distributions
        skewed_cols = []
        for col, stats in self.analyzer.column_stats.items():
            if 'skew' in stats.stats and abs(stats.stats['skew']) > 1.5:
                skewed_cols.append(col)
        
        if skewed_cols:
            recommendations.append(f"Consider transformation for skewed columns: {', '.join(skewed_cols[:3])}")
        
        if not recommendations:
            recommendations.append("Data quality appears good. Proceed with analysis.")
        
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def generate_html_report(self, include_visuals: bool = False, theme: str = 'creative') -> str:
        """
        Generate an HTML report.
        
        Parameters
        ----------
        include_visuals : bool
            Whether to include base64-encoded visualizations
        theme : str
            Report theme ('creative', 'professional', 'simple')
            
        Returns
        -------
        str
            HTML report as string
        """
        from jinja2 import Environment
        
        summary = self.analyzer.get_summary()
        
        # Select template based on theme
        if theme == 'creative':
            html_template = self._get_creative_template()
        elif theme == 'professional':
            html_template = self._get_professional_template()
        else:
            html_template = self._get_simple_template()
        
        # Prepare data for template
        template_data = {
            'dataset_name': self.analyzer.name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': summary,
            'issues': self.analyzer.issues,
            'missing_overview': summary['missing_data_overview'],
            'column_types': summary['column_types'],
            'visuals_base64': None,
        }
        
        # Add recommendations
        recommendations = []
        severity_counts = summary['issues_by_severity']
        
        if severity_counts.get('critical', 0) > 0:
            recommendations.append("Address critical issues before proceeding with analysis.")
        
        missing_overview = summary['missing_data_overview']
        if missing_overview['total_missing_percentage'] > 20:
            recommendations.append("High percentage of missing data. Consider data imputation or investigate data sources.")
        elif missing_overview['total_missing_percentage'] > 5:
            recommendations.append("Moderate missing data. Review patterns and consider appropriate handling methods.")
        
        # Check for skewed distributions
        skewed_cols = []
        for col, stats in self.analyzer.column_stats.items():
            if 'skew' in stats.stats and abs(stats.stats['skew']) > 1.5:
                skewed_cols.append(col)
        
        if skewed_cols:
            col_list = ', '.join(skewed_cols[:3])
            if len(skewed_cols) > 3:
                col_list += f' and {len(skewed_cols) - 3} more'
            recommendations.append(f"Consider transformation for skewed columns: {col_list}")
            
        # Gap 4: Auto-Fix / AI Suggestions (Heuristic)
        if summary['issues_by_severity']['critical'] > 0:
            recommendations.append("<b>Auto-Fix Suggestions:</b>")
            for issue in summary.get('issues', []):
                if issue.severity == 'critical':
                    if issue.issue_type == 'missing_values':
                        recommendations.append(f"• Column '{issue.column}': Impute with mean/median or drop if > 50% missing.")
                    elif issue.issue_type == 'outliers':
                        recommendations.append(f"• Column '{issue.column}': Cap values at 1.5*IQR or use robust scaling.")
            
            
        if not recommendations:
            recommendations.append("Data quality appears good. No specific actions required at this time.")
        
        template_data['recommendations'] = recommendations
        
        # Custom filters
        def comma_filter(value):
            return f"{value:,}"
        
        def int_filter(value):
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        
        # Create environment with filters
        env = Environment()
        env.filters['comma'] = comma_filter
        env.filters['int'] = int_filter
        
        # Create template from string
        template = env.from_string(html_template)
        
        html_report = template.render(**template_data)
        return html_report

    def save_report(self, output_path: str, format: str = 'html'):
        """
        Save report to file.
        
        Parameters
        ----------
        output_path : str
            Path to save the report
        format : str
            Report format ('html', 'text', 'json')
        """
        if format == 'html':
            report = self.generate_html_report()
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        elif format == 'text':
            report = self.generate_text_report()
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        elif format == 'json':
            summary = self.analyzer.get_summary()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"Report saved to {output_path}")
    def _get_creative_template(self) -> str:

        """Returns the creative/modern HTML template."""

        return '''

        <!DOCTYPE html>

        <html>

        <head>

            <title>DQ Report - {{ dataset_name }}</title>

            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">

            <style>

                :root {

                    --bg-color: #0f172a;

                    --card-bg: #1e293b;

                    --text-primary: #f8fafc;

                    --text-secondary: #94a3b8;

                    --accent: #38bdf8;

                    --accent-gradient: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);

                    --success: #22c55e;

                    --warning: #f59e0b;

                    --danger: #ef4444;

                    --border: #334155;

                }

                body {

                    font-family: 'Outfit', sans-serif;

                    background-color: var(--bg-color);

                    color: var(--text-primary);

                    margin: 0;

                    padding: 40px;

                    line-height: 1.6;

                }

                .container {

                    max-width: 1400px;

                    margin: 0 auto;

                }

                .header {

                    text-align: center;

                    margin-bottom: 60px;

                    padding: 40px;

                    background: rgba(30, 41, 59, 0.5);

                    backdrop-filter: blur(10px);

                    border-radius: 20px;

                    border: 1px solid var(--border);

                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);

                }

                h1 {

                    font-size: 3.5rem;

                    margin: 0;

                    background: var(--accent-gradient);

                    -webkit-background-clip: text;

                    -webkit-text-fill-color: transparent;

                    font-weight: 700;

                    letter-spacing: -1px;

                }

                .subtitle {

                    color: var(--text-secondary);

                    font-size: 1.2rem;

                    margin-top: 10px;

                }

                .section {

                    margin-bottom: 50px;

                }

                .section-title {

                    font-size: 1.8rem;

                    margin-bottom: 25px;

                    color: var(--text-primary);

                    border-left: 5px solid var(--accent);

                    padding-left: 15px;

                }

                .grid {

                    display: grid;

                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));

                    gap: 25px;

                }

                .card {

                    background-color: var(--card-bg);

                    border-radius: 15px;

                    padding: 25px;

                    border: 1px solid var(--border);

                    transition: transform 0.2s, box-shadow 0.2s;

                }

                .card:hover {

                    transform: translateY(-5px);

                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

                    border-color: var(--accent);

                }

                .metric-value {

                    font-size: 2.5rem;

                    font-weight: 700;

                    color: var(--text-primary);

                    margin: 10px 0;

                }

                .metric-label {

                    color: var(--text-secondary);

                    font-size: 0.9rem;

                    text-transform: uppercase;

                    letter-spacing: 1px;

                }

                

                /* Issues Table */

                .table-container {

                    background: var(--card-bg);

                    border-radius: 15px;

                    overflow: hidden;

                    border: 1px solid var(--border);

                }

                table {

                    width: 100%;

                    border-collapse: collapse;

                }

                th {

                    background: #253347;

                    padding: 15px;

                    text-align: left;

                    color: var(--accent);

                    font-weight: 600;

                }

                td {

                    padding: 15px;

                    border-top: 1px solid var(--border);

                    color: var(--text-secondary);

                }

                tr:hover td {

                    background: rgba(255, 255, 255, 0.02);

                    color: var(--text-primary);

                }

                

                /* Badges */

                .badge {

                    padding: 5px 12px;

                    border-radius: 20px;

                    font-size: 0.8rem;

                    font-weight: 600;

                }

                .badge.critical { background: rgba(239, 68, 68, 0.2); color: var(--danger); }

                .badge.warning { background: rgba(245, 158, 11, 0.2); color: var(--warning); }

                .badge.info { background: rgba(56, 189, 248, 0.2); color: var(--accent); }

                .badge.good { background: rgba(34, 197, 94, 0.2); color: var(--success); }

                

                .recommendation-card {

                    background: linear-gradient(90deg, rgba(56, 189, 248, 0.1) 0%, rgba(30, 41, 59, 0) 100%);

                    border-left: 4px solid var(--accent);

                    margin-bottom: 15px;

                    padding: 20px;

                }

                

                .details-box {

                    font-family: 'Consolas', monospace;

                    background: rgba(0, 0, 0, 0.2);

                    padding: 8px;

                    border-radius: 6px;

                    font-size: 0.85em;

                }

            </style>

        </head>

        <body>

            <div class="container">

                <div class="header">

                    <h1>{{ dataset_name }}</h1>

                    <div class="subtitle">Data Quality Dashboard &bull; Generated {{ timestamp }}</div>

                </div>

                

                <div class="section">

                    <div class="grid">

                        <div class="card">

                            <div class="metric-label">Total Rows</div>

                            <div class="metric-value" style="color: var(--accent)">{{ summary.dataset.rows|int|comma }}</div>

                        </div>

                        <div class="card">

                            <div class="metric-label">Columns</div>

                            <div class="metric-value">{{ summary.columns }}</div>

                        </div>

                        <div class="card">

                            <div class="metric-label">Total Cells</div>

                            <div class="metric-value">{{ summary.dataset.total_cells|int|comma }}</div>

                        </div>

                        <div class="card">

                            <div class="metric-label">Quality Score</div>

                            <div class="metric-value" style="color: {% if summary.issues_by_severity.critical > 0 %}var(--danger){% elif summary.issues_by_severity.warning > 0 %}var(--warning){% else %}var(--success){% endif %}">

                                {% if summary.issues_by_severity.critical > 0 %}POOR{% elif summary.issues_by_severity.warning > 0 %}FAIR{% else %}GOOD{% endif %}

                            </div>

                        </div>

                    </div>

                </div>

                

                <div class="grid" style="grid-template-columns: 2fr 1fr; margin-bottom: 50px;">

                    <div class="card">

                        <h3 class="section-title" style="font-size: 1.4rem; margin-top:0;">Issues Overview</h3>

                         <div class="grid" style="grid-template-columns: 1fr 1fr 1fr;">

                            <div style="text-align: center;">

                                <div style="font-size: 3rem; color: var(--danger); font-weight: bold;">{{ summary.issues_by_severity.critical }}</div>

                                <div class="metric-label">Critical</div>

                            </div>

                            <div style="text-align: center;">

                                <div style="font-size: 3rem; color: var(--warning); font-weight: bold;">{{ summary.issues_by_severity.warning }}</div>

                                <div class="metric-label">Warning</div>

                            </div>

                            <div style="text-align: center;">

                                <div style="font-size: 3rem; color: var(--accent); font-weight: bold;">{{ summary.issues_by_severity.info }}</div>

                                <div class="metric-label">Info</div>

                            </div>

                        </div>

                    </div>

                    

                    <div class="card">

                        <h3 class="section-title" style="font-size: 1.4rem; margin-top:0;">Missing Data</h3>

                        <div style="text-align: center; margin-top: 20px;">

                            <div style="font-size: 4rem; color: {% if missing_overview.total_missing_percentage > 5 %}var(--warning){% else %}var(--text-primary){% endif %}; font-weight: bold;">

                                {{ "%.1f"|format(missing_overview.total_missing_percentage) }}%

                            </div>

                            <div class="metric-label">Overall Missing</div>

                        </div>

                        <div style="margin-top: 20px; font-size: 0.9rem; color: var(--text-secondary); text-align: center;">

                            {{ missing_overview.total_missing_cells|int|comma }} missing cells

                        </div>

                    </div>

                </div>



                {% if issues %}

                <div class="section">

                    <h2 class="section-title">Detailed Issues</h2>

                    <div class="table-container">

                        <table>

                            <thead>

                                <tr>

                                    <th>Column</th>

                                    <th>Issue</th>

                                    <th>Severity</th>

                                    <th>Message</th>

                                    <th>Affected</th>

                                    <th>Details</th>

                                </tr>

                            </thead>

                            <tbody>

                                {% for issue in issues %}

                                <tr>

                                    <td style="font-weight: 600; color: var(--text-primary);">{{ issue.column }}</td>

                                    <td>{{ issue.issue_type|replace('_', ' ')|title }}</td>

                                    <td><span class="badge {{ issue.severity }}">{{ issue.severity|upper }}</span></td>

                                    <td>{{ issue.message }}</td>

                                    <td>

                                        {% if issue.affected_count > 0 %}

                                            {{ issue.affected_count|int|comma }} ({{ "%.1f"|format(issue.affected_percentage) }}%)

                                        {% else %}-{% endif %}

                                    </td>

                                    <td>

                                         {% if issue.details and (issue.details.examples or issue.details.outlier_examples) %}

                                            <div class="details-box">

                                                {% if issue.details.examples %}

                                                    {{ issue.details.examples|join(", ")|truncate(50) }}

                                                {% elif issue.details.outlier_examples %}

                                                     {{ issue.details.outlier_examples|join(", ")|truncate(50) }}

                                                {% endif %}

                                            </div>

                                         {% endif %}

                                    </td>

                                </tr>

                                {% endfor %}

                            </tbody>

                        </table>

                    </div>

                </div>

                {% endif %}

                

                <div class="section">

                    <h2 class="section-title">Smart Recommendations</h2>

                    {% if recommendations %}

                        {% for rec in recommendations %}

                        <div class="card recommendation-card">

                            <div style="display: flex; align-items: start; gap: 15px;">

                                <div style="background: var(--accent); color: white; width: 25px; height: 25px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">{{ loop.index }}</div>

                                <div>{{ rec }}</div>

                            </div>

                        </div>

                        {% endfor %}

                    {% else %}

                        <div class="card recommendation-card">

                            No functional changes needed. Data quality is excellent.

                        </div>

                    {% endif %}

                </div>

                

                <div class="footer">

                    PyDataQuality Report &bull; {{ dataset_name }}

                </div>

            </div>

        </body>

        </html>

        '''



    def _get_professional_template(self) -> str:

        """Returns the professional/PDF-optimized HTML template."""

        return '''

        <!DOCTYPE html>

        <html>

        <head>

            <title>DQ Report - {{ dataset_name }}</title>

            <link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">

            <style>

                body {

                    font-family: 'Open Sans', sans-serif;

                    line-height: 1.5;

                    color: #333;

                    max-width: 210mm; /* A4 Width */

                    margin: 0 auto;

                    padding: 40px;

                    background: white;

                }

                h1, h2, h3 {

                    font-family: 'Merriweather', serif;

                    color: #2c3e50;

                }

                h1 { border-bottom: 2px solid #2c3e50; padding-bottom: 10px; margin-bottom: 30px; }

                h2 { margin-top: 40px; border-bottom: 1px solid #eee; padding-bottom: 5px; }

                

                table {

                    width: 100%;

                    border-collapse: collapse;

                    margin: 20px 0;

                    font-size: 0.9rem;

                    page-break-inside: auto;

                }

                tr { page-break-inside: avoid; page-break-after: auto; }

                th {

                    border-bottom: 2px solid #333;

                    text-align: left;

                    padding: 8px;

                    font-weight: old;

                }

                td {

                    border-bottom: 1px solid #ddd;

                    padding: 8px;

                }

                

                .metric-box {

                    border: 1px solid #ddd;

                    padding: 15px;

                    margin-bottom: 20px;

                    background: #f9f9f9;

                }

                .metric-row { display: flex; justify-content: space-between; margin-bottom: 10px; }

                .label { font-weight: bold; color: #666; }

                

                .warning { color: #d35400; font-weight: bold; }

                .critical { color: #c0392b; font-weight: bold; }

                

                @media print {

                    body { padding: 0; max-width: 100%; }

                    .no-print { display: none; }

                }

            </style>

        </head>

        <body>

            <h1>Data Quality Assessment Report</h1>

            <p><strong>Dataset:</strong> {{ dataset_name }}<br>

            <strong>Date:</strong> {{ timestamp }}</p>

            

            <div class="metric-box">

                <div class="metric-row">

                    <span><strong>Rows:</strong> {{ summary.dataset.rows|int|comma }}</span>

                    <span><strong>Columns:</strong> {{ summary.columns }}</span>

                    <span><strong>Memory:</strong> {{ "%.2f"|format(summary.dataset.memory_usage_mb) }} MB</span>

                </div>

            </div>

            

            <h2>Executive Summary</h2>

            <p>

                The dataset contains <strong>{{ summary.dataset.rows|int|comma }}</strong> records. 

                Data quality analysis identified 

                <span class="critical">{{ summary.issues_by_severity.critical }} critical</span> and 

                <span class="warning">{{ summary.issues_by_severity.warning }} warning</span> issues.

                

                {% if missing_overview.total_missing_percentage > 5 %}

                Significant missing data was observed ({{ "%.1f"|format(missing_overview.total_missing_percentage) }}% overall).

                {% endif %}

            </p>

            

            {% if issues %}

            <h2>Detailed Findings</h2>

            <table>

                <thead>

                    <tr>

                        <th>Severity</th>

                        <th>Column</th>

                        <th>Issue</th>

                        <th>Impact</th>

                        <th>Details</th>

                    </tr>

                </thead>

                <tbody>

                    {% for issue in issues %}

                    {% if issue.severity in ['critical', 'warning'] %}

                    <tr>

                        <td class="{{ issue.severity }}">{{ issue.severity|upper }}</td>

                        <td>{{ issue.column }}</td>

                        <td>{{ issue.message }}</td>

                        <td>

                            {% if issue.affected_count > 0 %}

                            {{ issue.affected_count|int|comma }} rows ({{ "%.1f"|format(issue.affected_percentage) }}%)

                            {% endif %}

                        </td>

                        <td>

                            {% if issue.details and (issue.details.examples or issue.details.outlier_examples) %}

                            <div style="font-family: monospace; font-size: 0.8em; color: #555;">

                                {% if issue.details.examples %}

                                    {{ issue.details.examples|join(", ")|truncate(50) }}

                                {% elif issue.details.outlier_examples %}

                                     {{ issue.details.outlier_examples|join(", ")|truncate(50) }}

                                {% endif %}

                            </div>

                            {% endif %}

                        </td>

                    </tr>

                    {% endif %}

                    {% endfor %}

                </tbody>

            </table>

            {% endif %}

            

            <h2>Recommendation</h2>

            <ul>

            {% for rec in recommendations %}

                <li>{{ rec }}</li>

            {% endfor %}

            </ul>

            

            <div style="margin-top: 50px; border-top: 1px solid #ccc; padding-top: 10px; font-size: 0.8rem; color: #666; text-align: center;">

                Generated by PyDataQuality

            </div>

        </body>

        </html>

        '''



    def _get_simple_template(self) -> str:

        """Returns the original/simple HTML template."""

        return '''

        <!DOCTYPE html>

        <html>

        <head>

            <title>Data Quality Report - {{ dataset_name }}</title>

            <style>

                body {

                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;

                    line-height: 1.6;

                    color: #333;

                    max-width: 1400px;

                    margin: 0 auto;

                    padding: 20px;

                    background-color: #f8f9fa;

                }

                .header {

                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

                    color: white;

                    padding: 30px;

                    border-radius: 10px;

                    margin-bottom: 30px;

                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);

                }

                .section {

                    background: white;

                    padding: 25px;

                    border-radius: 8px;

                    margin-bottom: 25px;

                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);

                }

                .section-title {

                    color: #2c3e50;

                    border-bottom: 2px solid #3498db;

                    padding-bottom: 10px;

                    margin-top: 0;

                    margin-bottom: 20px;

                }

                .metric-grid {

                    display: grid;

                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));

                    gap: 20px;

                    margin-bottom: 20px;

                }

                .metric-card {

                    background: #f8f9fa;

                    padding: 20px;

                    border-radius: 8px;

                    text-align: center;

                    border-left: 4px solid #3498db;

                }

                .metric-value {

                    font-size: 2em;

                    font-weight: bold;

                    color: #2c3e50;

                    margin: 10px 0;

                }

                .metric-label {

                    color: #7f8c8d;

                    font-size: 0.9em;

                    text-transform: uppercase;

                    letter-spacing: 1px;

                }

                .issue-critical {

                    color: #e74c3c;

                    font-weight: bold;

                }

                .issue-warning {

                    color: #f39c12;

                    font-weight: bold;

                }

                .issue-info {

                    color: #3498db;

                }

                table {

                    width: 100%;

                    border-collapse: collapse;

                    margin: 20px 0;

                    font-size: 0.9em;

                }

                th {

                    background-color: #f2f6fc;

                    color: #2c3e50;

                    font-weight: 600;

                    padding: 12px;

                    text-align: left;

                    border-bottom: 2px solid #e0e6ef;

                }

                td {

                    padding: 12px;

                    border-bottom: 1px solid #e0e6ef;

                    vertical-align: top;

                }

                tr:hover {

                    background-color: #f8fafc;

                }

                .status-badge {

                    display: inline-block;

                    padding: 4px 12px;

                    border-radius: 20px;

                    font-size: 0.85em;

                    font-weight: 600;

                }

                .status-critical {

                    background-color: #fee;

                    color: #c00;

                }

                .status-warning {

                    background-color: #fff3cd;

                    color: #856404;

                }

                .status-good {

                    background-color: #d4edda;

                    color: #155724;

                }

                .visualization {

                    margin: 30px 0;

                    text-align: center;

                }

                .visualization img {

                    max-width: 100%;

                    height: auto;

                    border-radius: 8px;

                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);

                }

                .recommendation {

                    background: #e3f2fd;

                    padding: 15px;

                    border-radius: 6px;

                    margin: 10px 0;

                    border-left: 4px solid #2196f3;

                }

                .details-cell {

                    max-width: 300px;

                    word-wrap: break-word;

                    font-size: 0.85em;

                    color: #666;

                }

                .footer {

                    text-align: center;

                    margin-top: 40px;

                    padding-top: 20px;

                    border-top: 1px solid #e0e6ef;

                    color: #7f8c8d;

                    font-size: 0.9em;

                    margin-bottom: 20px;

                }

                .timestamp {

                    font-size: 0.9em;

                    color: #7f8c8d;

                    margin-bottom: 20px;

                }

                .details-examples {

                    background: #f8f9fa;

                    padding: 8px;

                    border-radius: 4px;

                    margin-top: 5px;

                    font-family: monospace;

                    font-size: 0.85em;

                }

            </style>

        </head>

        <body>

            <div class="header">

                <h1>Data Quality Analysis Report</h1>

                <h2>{{ dataset_name }}</h2>

                <div class="timestamp">Generated on {{ timestamp }}</div>

            </div>

            

            <div class="section">

                <h2 class="section-title">Executive Summary</h2>

                <div class="metric-grid">

                    <div class="metric-card">

                        <div class="metric-label">Rows</div>

                        <div class="metric-value">{{ summary.dataset.rows|int|comma }}</div>

                    </div>

                    <div class="metric-card">

                        <div class="metric-label">Columns</div>

                        <div class="metric-value">{{ summary.columns }}</div>

                    </div>

                    <div class="metric-card">

                        <div class="metric-label">Memory Usage</div>

                        <div class="metric-value">{{ "%.2f"|format(summary.dataset.memory_usage_mb) }} MB</div>

                    </div>

                    <div class="metric-card">

                        <div class="metric-label">Total Cells</div>

                        <div class="metric-value">{{ summary.dataset.total_cells|int|comma }}</div>

                    </div>

                </div>

            </div>

            

            <div class="section">

                <h2 class="section-title">Data Quality Issues</h2>

                <div class="metric-grid">

                    <div class="metric-card">

                        <div class="metric-label">Critical Issues</div>

                        <div class="metric-value issue-critical">{{ summary.issues_by_severity.critical }}</div>

                    </div>

                    <div class="metric-card">

                        <div class="metric-label">Warning Issues</div>

                        <div class="metric-value issue-warning">{{ summary.issues_by_severity.warning }}</div>

                    </div>

                    <div class="metric-card">

                        <div class="metric-label">Informational</div>

                        <div class="metric-value issue-info">{{ summary.issues_by_severity.info }}</div>

                    </div>

                    <div class="metric-card">

                        <div class="metric-label">Overall Status</div>

                        <div class="metric-value">

                            {% if summary.issues_by_severity.critical > 0 %}

                                <span class="status-badge status-critical">Needs Attention</span>

                            {% elif summary.issues_by_severity.warning > 0 %}

                                <span class="status-badge status-warning">Review Recommended</span>

                            {% else %}

                                <span class="status-badge status-good">Good Quality</span>

                            {% endif %}

                        </div>

                    </div>

                </div>

                

                {% if issues %}

                <table>

                    <thead>

                        <tr>

                            <th>Column</th>

                            <th>Issue Type</th>

                            <th>Severity</th>

                            <th>Message</th>

                            <th>Affected</th>

                            <th>Details</th>

                        </tr>

                    </thead>

                    <tbody>

                        {% for issue in issues %}

                        <tr>

                            <td>{{ issue.column }}</td>

                            <td>{{ issue.issue_type|replace('_', ' ')|title }}</td>

                            <td>

                                <span class="status-badge status-{{ issue.severity }}">

                                    {{ issue.severity|title }}

                                </span>

                            </td>

                            <td>{{ issue.message }}</td>

                            <td>

                                {% if issue.affected_count > 0 %}

                                {{ issue.affected_count|int|comma }} ({{ "%.1f"|format(issue.affected_percentage) }}%)

                                {% else %}

                                -

                                {% endif %}

                            </td>

                            <td class="details-cell">

                                {% if issue.details %}

                                    {% if issue.details.examples %}

                                        Examples: {{ issue.details.examples|join(", ") }}

                                    {% elif issue.details.outlier_examples %}

                                        Bounds: [{{ "%.2f"|format(issue.details.lower_bound) }}, {{ "%.2f"|format(issue.details.upper_bound) }}]

                                        Examples: {{ issue.details.outlier_examples|join(", ") }}

                                    {% elif issue.details.placeholder_counts %}

                                        {{ issue.details.placeholder_counts|join("; ") }}

                                    {% elif issue.details.skewness %}

                                        Skewness: {{ "%.2f"|format(issue.details.skewness) }}

                                    {% else %}

                                        <!-- Other details -->

                                    {% endif %}

                                {% else %}

                                -

                                {% endif %}

                            </td>

                        </tr>

                        {% endfor %}

                    </tbody>

                </table>

                {% else %}

                <p>No issues found. Data quality appears good.</p>

                {% endif %}

            </div>

            

            <div class="section">

                <h2 class="section-title">Missing Data Analysis</h2>

                <div class="metric-grid">

                    <div class="metric-card">

                        <div class="metric-label">Columns with Missing Values</div>

                        <div class="metric-value">{{ missing_overview.columns_with_missing }}</div>

                    </div>

                    <div class="metric-card">

                        <div class="metric-label">Total Missing Cells</div>

                        <div class="metric-value">{{ missing_overview.total_missing_cells|int|comma }}</div>

                    </div>

                    <div class="metric-card">

                        <div class="metric-label">Overall Missing %</div>

                        <div class"metric-value">{{ "%.2f"|format(missing_overview.total_missing_percentage) }}%</div>

                    </div>

                </div>

                

                {% if missing_overview.columns %}

                <table>

                    <thead>

                        <tr>

                            <th>Column</th>

                            <th>Missing Count</th>

                            <th>Missing Percentage</th>

                            <th>Status</th>

                        </tr>

                    </thead>

                    <tbody>

                        {% for col in missing_overview.columns %}

                        <tr>

                            <td>{{ col.column }}</td>

                            <td>{{ col.missing_count|int|comma }}</td>

                            <td>{{ "%.1f"|format(col.missing_percentage) }}%</td>

                            <td>

                                {% if col.missing_percentage > 30 %}

                                <span class="status-badge status-critical">Critical</span>

                                {% elif col.missing_percentage > 5 %}

                                <span class="status-badge status-warning">Warning</span>

                                {% else %}

                                <span class="status-badge status-good">Acceptable</span>

                                {% endif %}

                            </td>

                        </tr>

                        {% endfor %}

                    </tbody>

                </table>

                {% else %}

                <p>No missing values found in the dataset.</p>

                {% endif %}

            </div>

            

            <div class="section">

                <h2 class="section-title">Data Types Overview</h2>

                <table>

                    <thead>

                        <tr>

                            <th>Data Type</th>

                            <th>Count</th>

                            <th>Percentage</th>

                        </tr>

                    </thead>

                    <tbody>

                        {% for dtype, count in column_types.items() %}

                        <tr>

                            <td>{{ dtype|title }}</td>

                            <td>{{ count }}</td>

                            <td>{{ "%.1f"|format(count / summary.columns * 100) }}%</td>

                        </tr>

                        {% endfor %}

                    </tbody>

                </table>

            </div>

            

            <div class="section">

                <h2 class="section-title">Recommendations</h2>

                {% if recommendations %}

                    {% for rec in recommendations %}

                    <div class="recommendation">

                        {{ loop.index }}. {{ rec }}

                    </div>

                    {% endfor %}

                {% else %}

                    <p>No specific recommendations. Data quality appears satisfactory.</p>

                {% endif %}

            </div>

            

            <div class="footer">

                <p>Report generated by PyDataQuality v0.1.0</p>

                <p>For questions or issues, please contact the data team.</p>

            </div>

        </body>

        </html>

        '''
        
