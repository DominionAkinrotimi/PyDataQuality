# pydataquality/utils.py
"""
Utility functions for PyDataQuality.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import warnings


def detect_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Detect and categorize columns by their data types.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe
        
    Returns
    -------
    dict
        Dictionary with column type categories and lists of column names
    """
    column_types = {
        'numeric': [],
        'categorical': [],
        'datetime': [],
        'boolean': [],
        'text': [],
        'other': []
    }
    
    for column in df.columns:
        dtype = str(df[column].dtype)
        
        # Check for numeric types
        if pd.api.types.is_numeric_dtype(df[column]):
            column_types['numeric'].append(column)
        
        # Check for datetime types
        elif pd.api.types.is_datetime64_any_dtype(df[column]):
            column_types['datetime'].append(column)
        
        # Check for boolean types
        elif pd.api.types.is_bool_dtype(df[column]):
            column_types['boolean'].append(column)
        
        # Check for categorical/text types
        elif pd.api.types.is_string_dtype(df[column]) or pd.api.types.is_categorical_dtype(df[column]):
            # Try to distinguish between categorical and text
            unique_count = df[column].nunique()
            total_count = len(df[column])
            
            if unique_count / total_count < 0.1:  # Less than 10% unique values
                column_types['categorical'].append(column)
            elif unique_count > 50:  # Many unique values
                column_types['text'].append(column)
            else:
                column_types['categorical'].append(column)
        
        else:
            column_types['other'].append(column)
    
    return column_types


def sample_dataframe(df: pd.DataFrame, n_samples: int = 1000, 
                    random_state: int = 42, stratify_by: str = None) -> pd.DataFrame:
    """
    Sample rows from dataframe for faster analysis.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe
    n_samples : int, optional
        Number of samples to take
    random_state : int, optional
        Random seed for reproducibility
    stratify_by : str, optional
        Column name to stratify sampling by
        
    Returns
    -------
    pandas.DataFrame
        Sampled dataframe
    """
    if len(df) <= n_samples:
        return df.copy()
    
    if stratify_by and stratify_by in df.columns:
        # Check if we can stratify (enough samples per class)
        try:
            # Determine sample rate
            sample_rate = n_samples / len(df)
            return df.groupby(stratify_by, group_keys=False).apply(
                lambda x: x.sample(frac=sample_rate, random_state=random_state)
            )
        except Exception as e:
            warnings.warn(f"Stratified sampling failed: {e}. Falling back to random sampling.")
    
    return df.sample(n=min(n_samples, len(df)), random_state=random_state)


def sample_large_dataset(filepath: str, n_samples: int = 1000, 
                        chunksize: int = 100000) -> pd.DataFrame:
    """
    Sample from a large file by reading in chunks.
    
    Parameters
    ----------
    filepath : str
        Path to the large CSV file
    n_samples : int
        Target number of samples
    chunksize : int
        Number of rows to read per chunk
        
    Returns
    -------
    pandas.DataFrame
        Sampled dataframe
    """
    # First estimate total rows (optional, but good for reservoir sampling)
    # For simplicity, we'll use a reservoir-like approach
    sampled_chunks = []
    
    try:
        # Read first chunk to get columns and likely types
        for chunk in pd.read_csv(filepath, chunksize=chunksize):
            # Simple random sample from each chunk
            # We take a bit more than needed to ensure we have enough coverage
            chunk_sample = chunk.sample(frac=0.1, random_state=42) 
            sampled_chunks.append(chunk_sample)
            
            # Stop if we have way more than needed (simple heuristic)
            if sum(len(c) for c in sampled_chunks) > n_samples * 5:
                break
                
        full_sample = pd.concat(sampled_chunks, ignore_index=True)
        
        # Final sample to exact number
        if len(full_sample) > n_samples:
            return full_sample.sample(n=n_samples, random_state=42)
        return full_sample
        
    except Exception as e:
        warnings.warn(f"Batch sampling failed: {e}")
        return pd.DataFrame()


def load_rules_from_yaml(filepath: str) -> Dict[str, Any]:
    """
    Load validation rules from a YAML file.
    
    Parameters
    ----------
    filepath : str
        Path to YAML config file
        
    Returns
    -------
    dict
        Rules dictionary
    """
    import yaml
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        warnings.warn("PyYAML not installed. Please install it to use YAML config: pip install PyYAML")
        return {}
    except Exception as e:
        warnings.warn(f"Failed to load rules: {e}")
        return {}

def validate_thresholds(thresholds: Dict[str, float]) -> Dict[str, float]:
    """
    Validate and set default thresholds for data quality checks.
    
    Parameters
    ----------
    thresholds : dict
        User-provided thresholds
        
    Returns
    -------
    dict
        Validated thresholds with defaults
    """
    default_thresholds = {
        'missing_critical': 0.3,
        'missing_warning': 0.05,
        'outlier_threshold': 1.5,
        'skew_threshold': 1.0,
        'unique_threshold': 0.01,
        'zero_threshold': 0.8,
    }
    
    # Update defaults with user values
    validated = default_thresholds.copy()
    for key, value in thresholds.items():
        if key in validated:
            if 0 <= value <= 1:
                validated[key] = value
            else:
                warnings.warn(f"Threshold {key} value {value} should be between 0 and 1. Using default.")
    
    return validated


def format_memory_size(bytes: float) -> str:
    """
    Format memory size in human-readable format.
    
    Parameters
    ----------
    bytes : float
        Memory size in bytes
        
    Returns
    -------
    str
        Formatted memory size
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


def create_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create basic summary statistics for a dataframe.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe
        
    Returns
    -------
    dict
        Summary statistics
    """
    summary = {
        'shape': df.shape,
        'total_cells': df.shape[0] * df.shape[1],
        'memory_usage_bytes': df.memory_usage(deep=True).sum(),
        'dtypes_count': df.dtypes.value_counts().to_dict(),
        'columns': list(df.columns),
        'index_type': str(type(df.index)),
    }
    
    # Add memory usage in human-readable format
    summary['memory_usage_readable'] = format_memory_size(summary['memory_usage_bytes'])
    
    return summary


def find_duplicate_columns(df: pd.DataFrame, threshold: float = 0.95) -> List[List[str]]:
    """
    Find columns with high correlation or similarity.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe
    threshold : float, optional
        Similarity threshold (0-1)
        
    Returns
    -------
    list
        List of groups of duplicate/similar columns
    """
    duplicate_groups = []
    processed_columns = set()
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) < 2:
        return duplicate_groups
    
    # Calculate correlation matrix
    corr_matrix = df[numeric_cols].corr().abs()
    
    for i, col1 in enumerate(numeric_cols):
        if col1 in processed_columns:
            continue
        
        duplicates = [col1]
        
        for j, col2 in enumerate(numeric_cols[i+1:], start=i+1):
            if corr_matrix.iloc[i, j] > threshold:
                duplicates.append(col2)
                processed_columns.add(col2)
        
        if len(duplicates) > 1:
            duplicate_groups.append(duplicates)
        
        processed_columns.add(col1)
    
    return duplicate_groups


def detect_potential_ids(df: pd.DataFrame) -> List[str]:
    """
    Detect columns that might be ID columns.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe
        
    Returns
    -------
    list
        List of potential ID column names
    """
    potential_ids = []
    
    for column in df.columns:
        # Check for common ID patterns in column names
        col_lower = column.lower()
        id_keywords = ['id', 'code', 'num', 'no', 'key', 'index', 'ref']
        
        if any(keyword in col_lower for keyword in id_keywords):
            # Check if values are unique or nearly unique
            unique_count = df[column].nunique()
            total_count = len(df[column])
            uniqueness_ratio = unique_count / total_count
            
            if uniqueness_ratio > 0.95:  # More than 95% unique values
                potential_ids.append({
                    'column': column,
                    'uniqueness_ratio': uniqueness_ratio,
                    'dtype': str(df[column].dtype)
                })
    
    return potential_ids


def check_date_consistency(df: pd.DataFrame, date_columns: List[str]) -> Dict[str, Any]:
    """
    Check consistency of date columns.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe
    date_columns : list
        List of date column names
        
    Returns
    -------
    dict
        Date consistency checks
    """
    results = {}
    
    for col in date_columns:
        if col not in df.columns:
            continue
        
        try:
            dates = pd.to_datetime(df[col], errors='coerce')
            valid_dates = dates.dropna()
            
            if len(valid_dates) == 0:
                results[col] = {'status': 'no_valid_dates'}
                continue
            
            date_stats = {
                'min_date': valid_dates.min().isoformat(),
                'max_date': valid_dates.max().isoformat(),
                'date_range_days': (valid_dates.max() - valid_dates.min()).days,
                'future_dates': int((valid_dates > pd.Timestamp.now()).sum()),
                'past_century_dates': int((valid_dates < pd.Timestamp('1900-01-01')).sum()),
                'valid_date_count': len(valid_dates),
                'invalid_date_count': len(dates) - len(valid_dates),
                'format_issues': []
            }
            
            # Check for mixed date formats (if column is string)
            if pd.api.types.is_string_dtype(df[col]):
                sample_dates = df[col].dropna().head(100)
                unique_formats = set()
                
                for date_str in sample_dates:
                    # Try to detect common separators
                    if '/' in date_str:
                        unique_formats.add('contains /')
                    elif '-' in date_str:
                        unique_formats.add('contains -')
                    elif '.' in date_str:
                        unique_formats.add('contains .')
                
                if len(unique_formats) > 1:
                    date_stats['format_issues'].append(f'Multiple date separators detected: {unique_formats}')
            
            results[col] = date_stats
            
        except Exception as e:
            results[col] = {'status': 'error', 'error': str(e)}
    
    return results