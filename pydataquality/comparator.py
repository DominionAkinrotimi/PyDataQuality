import pandas as pd
from typing import Dict, List, Any
from .analyzer import DataQualityAnalyzer 

class DataQualityComparator:
    """
    Compare two DataQualityAnalyzer results to detect data drift.
    """
    
    def __init__(self, reference_analyzer: DataQualityAnalyzer, current_analyzer: DataQualityAnalyzer):
        self.ref = reference_analyzer
        self.curr = current_analyzer
        
    def compare_statistics(self) -> pd.DataFrame:
        """
        Compare basic statistics between reference and current datasets.
        """
        comparison_data = []
        
        # Get common numeric columns
        ref_cols = set(self.ref.column_stats.keys())
        curr_cols = set(self.curr.column_stats.keys())
        common_cols = ref_cols.intersection(curr_cols)
        
        for col in common_cols:
            ref_stats = self.ref.column_stats[col].stats
            curr_stats = self.curr.column_stats[col].stats
            
            if 'mean' in ref_stats and 'mean' in curr_stats:
                comparison_data.append({
                    'column': col,
                    'ref_mean': ref_stats['mean'],
                    'curr_mean': curr_stats['mean'],
                    'pct_change': ((curr_stats['mean'] - ref_stats['mean']) / ref_stats['mean']) * 100 if ref_stats['mean'] != 0 else 0
                })
                
        return pd.DataFrame(comparison_data)

def compare_reports(analyzer_a, analyzer_b):
    """
    Convenience function to compare two analyzers.
    """
    comparator = DataQualityComparator(analyzer_a, analyzer_b)
    return comparator.compare_statistics()
