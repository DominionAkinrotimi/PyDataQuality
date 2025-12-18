"""
PyDataQuality - A comprehensive data quality analysis tool for Python.
"""

__version__ = '0.1.4'
__author__ = 'Dominion Akinrotimi'

from .analyzer import DataQualityAnalyzer
from .reporter import QualityReportGenerator
from .visualizer import DataQualityVisualizer
from .utils import (
    sample_dataframe, 
    sample_large_dataset, 
    detect_column_types, 
    detect_potential_ids,
    format_memory_size,
    validate_thresholds,
    find_duplicate_columns,
    load_rules_from_yaml
)
from .comparator import compare_reports
from .comparator import compare_reports

# Convenience functions
def analyze_dataframe(df, name="Dataset", verbose=False, config=None):
    """
    Convenience function to analyze a DataFrame.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to analyze
    name : str
        Name of the dataset
    verbose : bool
        Whether to print progress
    config : dict
        Custom configuration settings (optional)
        
    Returns
    -------
    DataQualityAnalyzer
        Analyzer instance
    """
    analyzer = DataQualityAnalyzer(df, name=name, config=config)
    # Analysis is triggered in __init__
    return analyzer

def quick_quality_check(df, name="Dataset"):
    """
    Quick quality check for a DataFrame.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to analyze
    name : str
        Name of the dataset
        
    Returns
    -------
    dict
        Summary of quality issues
    """
    analyzer = DataQualityAnalyzer(df, name=name)
    return analyzer.get_summary()

def generate_report(analyzer, output_path=None, format='html', theme='professional'):
    """
    Generate a report from analyzer and optionally save to file.
    
    Parameters
    ----------
    analyzer : DataQualityAnalyzer
        Analyzer instance
    output_path : str, optional
        Path to save the report
    format : str
        Report format ('html', 'json', 'text')
    theme : str
        HTML report theme ('professional', 'creative', 'simple')
        Default is 'professional' for clean PDF exports
        
    Returns
    -------
    str
        Report content
    """
    reporter = QualityReportGenerator(analyzer)
    
    content = ""
    if format == 'html':
        content = reporter.generate_html_report(theme=theme)
    elif format == 'json':
        import json
        summary = analyzer.get_summary()
        content = json.dumps(summary, indent=2, default=str)
    elif format == 'text':
        content = reporter.generate_text_report()
    elif format == 'csv':
        raise NotImplementedError("CSV export not yet implemented")
    else:
        raise ValueError(f"Unsupported format: {format}")
        
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    return content

def create_visual_report(analyzer, show_plots=True, save_path=None):
    """
    Create visual report from analyzer.
    
    Parameters
    ----------
    analyzer : DataQualityAnalyzer
        Analyzer instance
    show_plots : bool
        Whether to display plots (not used in current implementation)
    save_path : str, optional
        Path to save the report images
        
    Returns
    -------
    DataQualityVisualizer
        Visualizer instance
    """
    visualizer = DataQualityVisualizer(analyzer)
    visualizer.create_comprehensive_report(save_path=save_path)
    return visualizer

def show_report(analyzer, theme='creative'):
    """
    Render quality report in Jupyter/Colab notebook.
    
    Parameters
    ----------
    analyzer : DataQualityAnalyzer
        Analyzer instance
    theme : str
        Report theme ('creative', 'professional', 'simple')
    """
    from IPython.display import HTML, display
    reporter = QualityReportGenerator(analyzer)
    html = reporter.generate_html_report(theme=theme)
    display(HTML(html))

def generate_ai_prompt(analyzer):
    """
    Generate an AI remediation prompt for fixing data quality issues.
    
    This creates a prompt that can be copied to an AI assistant (like ChatGPT,
    Claude, or Gemini) to get automated code for fixing detected quality issues.
    
    Parameters
    ----------
    analyzer : DataQualityAnalyzer
        Analyzer instance with detected issues
        
    Returns
    -------
    str
        AI remediation prompt text
        
    Example
    -------
    >>> analyzer = pdq.analyze_dataframe(df)
    >>> prompt = pdq.generate_ai_prompt(analyzer)
    >>> print(prompt)
    """
    reporter = QualityReportGenerator(analyzer)
    return reporter.generate_ai_remediation_prompt()
