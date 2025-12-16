# pydataquality/visualizer.py
"""
Data visualization module for quality analysis.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import seaborn as sns

from .config import VISUAL_CONFIG
from .analyzer import DataQualityAnalyzer, QualityIssue


class DataQualityVisualizer:
    """
    Visualization module for data quality analysis results.
    """
    
    def __init__(self, analyzer: DataQualityAnalyzer):
        self.analyzer = analyzer
        self.figures = {}
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8-whitegrid')
        self._setup_colors()
    
    def _setup_colors(self):
        """Setup color schemes for visualizations."""
        self.colors = {
            'critical': '#d62728',    # Red
            'warning': '#ff7f0e',     # Orange
            'info': '#1f77b4',        # Blue
            'valid': '#2ca02c',       # Green
            'missing': '#7f7f7f',     # Gray
        }
    
    def create_missing_values_matrix(self, figsize: Tuple = None) -> plt.Figure:
        """
        Create a heatmap showing missing value patterns.
        
        Parameters
        ----------
        figsize : tuple, optional
            Figure size (width, height)
            
        Returns
        -------
        matplotlib.figure.Figure
            The generated figure
        """
        if figsize is None:
            figsize = VISUAL_CONFIG['figure_size']
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create binary matrix (1 = missing, 0 = present)
        missing_matrix = self.analyzer.df.isnull().astype(int)
        
        # Create heatmap
        sns.heatmap(missing_matrix.T,  # Transpose to have columns as y-axis
                   cmap=['white', self.colors['missing']],
                   cbar_kws={'label': 'Missing Values'},
                   linewidths=0.5,
                   linecolor='lightgray',
                   ax=ax)
        
        ax.set_title(f'Missing Value Patterns - {self.analyzer.name}', fontsize=14, pad=20)
        ax.set_xlabel('Row Index')
        ax.set_ylabel('Columns')
        
        # Improve readability
        ax.tick_params(axis='y', rotation=0)
        
        plt.tight_layout()
        
        self.figures['missing_matrix'] = fig
        return fig
    
    def create_issues_summary_chart(self, figsize: Tuple = None) -> plt.Figure:
        """
        Create a bar chart showing issues by severity and type.
        
        Parameters
        ----------
        figsize : tuple, optional
            Figure size (width, height)
            
        Returns
        -------
        matplotlib.figure.Figure
            The generated figure
        """
        if figsize is None:
            figsize = (10, 6)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Plot 1: Issues by severity
        severity_counts = self.analyzer._count_issues_by_severity()
        severities = list(severity_counts.keys())
        counts = list(severity_counts.values())
        
        colors = [self.colors[sev] for sev in severities]
        bars1 = ax1.bar(severities, counts, color=colors, alpha=0.8)
        
        ax1.set_title('Issues by Severity', fontsize=12)
        ax1.set_xlabel('Severity')
        ax1.set_ylabel('Count')
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Plot 2: Issues by type
        type_counts = self.analyzer._count_issues_by_type()
        if type_counts:
            types = list(type_counts.keys())
            type_counts_vals = list(type_counts.values())
            
            # Sort by count
            sorted_idx = np.argsort(type_counts_vals)[::-1]
            types = [types[i] for i in sorted_idx]
            type_counts_vals = [type_counts_vals[i] for i in sorted_idx]
            
            # Limit to top 10 types for readability
            if len(types) > 10:
                types = types[:10]
                type_counts_vals = type_counts_vals[:10]
                types[-1] = 'Other'
                type_counts_vals[-1] = sum(type_counts_vals[10:])
            
            bars2 = ax2.barh(range(len(types)), type_counts_vals, 
                           color=self.colors['info'], alpha=0.8)
            
            ax2.set_title('Top Issue Types', fontsize=12)
            ax2.set_xlabel('Count')
            ax2.set_yticks(range(len(types)))
            ax2.set_yticklabels(types)
            
            # Add value labels
            for i, bar in enumerate(bars2):
                width = bar.get_width()
                ax2.text(width + 0.5, bar.get_y() + bar.get_height()/2.,
                        f'{int(width)}', ha='left', va='center')
        else:
            ax2.text(0.5, 0.5, 'No Issues Found', 
                    ha='center', va='center', transform=ax2.transAxes)
        
        plt.suptitle(f'Data Quality Issues Summary - {self.analyzer.name}', fontsize=14)
        plt.tight_layout()
        
        self.figures['issues_summary'] = fig
        return fig
    
    def create_missing_values_distribution(self, figsize: Tuple = None) -> plt.Figure:
        """
        Create a bar chart showing missing values per column.
        
        Parameters
        ----------
        figsize : tuple, optional
            Figure size (width, height)
            
        Returns
        -------
        matplotlib.figure.Figure
            The generated figure
        """
        if figsize is None:
            figsize = (12, 6)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get columns with missing values
        missing_data = self.analyzer._get_missing_data_overview()
        columns_data = missing_data['columns']
        
        if not columns_data:
            ax.text(0.5, 0.5, 'No Missing Values Found', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Missing Values Distribution - {self.analyzer.name}', fontsize=14)
            plt.tight_layout()
            return fig
        
        # Prepare data for plotting
        columns = [item['column'] for item in columns_data]
        percentages = [item['missing_percentage'] for item in columns_data]
        counts = [item['missing_count'] for item in columns_data]
        
        # Create color based on severity
        colors = []
        for pct in percentages:
            if pct > 30:  # Critical
                colors.append(self.colors['critical'])
            elif pct > 5:  # Warning
                colors.append(self.colors['warning'])
            else:  # Info
                colors.append(self.colors['info'])
        
        # Create horizontal bar chart
        y_pos = np.arange(len(columns))
        bars = ax.barh(y_pos, percentages, color=colors, alpha=0.8)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(columns)
        ax.invert_yaxis()  # Highest percentage at top
        
        ax.set_xlabel('Missing Percentage (%)')
        ax.set_title(f'Missing Values Distribution - {self.analyzer.name}', fontsize=14)
        
        # Add value labels
        for i, (bar, pct, count) in enumerate(zip(bars, percentages, counts)):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2.,
                   f'{pct:.1f}% ({count})', ha='left', va='center')
        
        # Add threshold lines
        ax.axvline(x=5, color=self.colors['warning'], linestyle='--', alpha=0.5, label='Warning threshold (5%)')
        ax.axvline(x=30, color=self.colors['critical'], linestyle='--', alpha=0.5, label='Critical threshold (30%)')
        ax.legend()
        
        plt.tight_layout()
        
        self.figures['missing_distribution'] = fig
        return fig
    
    def create_numeric_distributions(self, columns: List[str] = None, 
                                    figsize: Tuple = None) -> plt.Figure:
        """
        Create distribution plots for numeric columns.
        
        Parameters
        ----------
        columns : list of str, optional
            Specific columns to plot. If None, plots all numeric columns.
        figsize : tuple, optional
            Figure size (width, height)
            
        Returns
        -------
        matplotlib.figure.Figure
            The generated figure
        """
        if columns is None:
            # Get all numeric columns
            numeric_cols = self.analyzer.df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            numeric_cols = [col for col in columns if col in self.analyzer.df.columns]
        
        if not numeric_cols:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'No Numeric Columns Found', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Numeric Distributions - {self.analyzer.name}', fontsize=14)
            plt.tight_layout()
            return fig
        
        # Determine grid layout
        n_cols = min(3, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        if figsize is None:
            figsize = (5 * n_cols, 4 * n_rows)
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten() if isinstance(axes, np.ndarray) else [axes]
        
        for idx, col in enumerate(numeric_cols):
            if idx >= len(axes):
                break
                
            ax = axes[idx]
            data = self.analyzer.df[col].dropna()
            
            if len(data) == 0:
                ax.text(0.5, 0.5, 'No Data', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(col, fontsize=10)
                continue
            
            # Create histogram
            n_bins = min(50, len(data) // 10)
            n_bins = max(10, n_bins)
            
            ax.hist(data, bins=n_bins, alpha=0.7, color=self.colors['info'], 
                   edgecolor='white', linewidth=0.5)
            
            # Add vertical lines for statistics
            mean_val = data.mean()
            median_val = data.median()
            
            ax.axvline(mean_val, color=self.colors['critical'], linestyle='-', 
                      linewidth=1.5, alpha=0.7, label=f'Mean: {mean_val:.2f}')
            ax.axvline(median_val, color=self.colors['warning'], linestyle='--', 
                      linewidth=1.5, alpha=0.7, label=f'Median: {median_val:.2f}')
            
            # Add boxplot inset
            box_ax = ax.inset_axes([0.65, 0.65, 0.3, 0.3])
            box_ax.boxplot(data, vert=True, patch_artist=True,
                          boxprops=dict(facecolor=self.colors['info'], alpha=0.7))
            box_ax.set_xticks([])
            box_ax.set_yticks([])
            
            ax.set_title(f'{col}\n(n={len(data):,})', fontsize=10)
            ax.set_xlabel('Value')
            ax.set_ylabel('Frequency')
            
            # Add skewness info
            skewness = data.skew()
            skew_text = f'Skew: {skewness:.2f}'
            if abs(skewness) > 1:
                skew_text += '\n(Highly skewed)'
            elif abs(skewness) > 0.5:
                skew_text += '\n(Moderately skewed)'
            
            ax.text(0.05, 0.95, skew_text, transform=ax.transAxes,
                   fontsize=8, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Hide unused subplots
        for idx in range(len(numeric_cols), len(axes)):
            axes[idx].axis('off')
        
        plt.suptitle(f'Numeric Distributions - {self.analyzer.name}', fontsize=14, y=1.02)
        plt.tight_layout()
        
        self.figures['numeric_distributions'] = fig
        return fig
    
    def create_outlier_detection_plot(self, columns: List[str] = None,
                                     figsize: Tuple = None) -> plt.Figure:
        """
        Create boxplots for outlier detection.
        
        Parameters
        ----------
        columns : list of str, optional
            Specific columns to plot. If None, plots all numeric columns.
        figsize : tuple, optional
            Figure size (width, height)
            
        Returns
        -------
        matplotlib.figure.Figure
            The generated figure
        """
        if columns is None:
            numeric_cols = self.analyzer.df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            numeric_cols = [col for col in columns if col in self.analyzer.df.columns]
        
        if not numeric_cols:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'No Numeric Columns Found', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Outlier Detection - {self.analyzer.name}', fontsize=14)
            plt.tight_layout()
            return fig
        
        # Determine grid layout
        n_cols = min(3, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        if figsize is None:
            figsize = (5 * n_cols, 4 * n_rows)
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten() if isinstance(axes, np.ndarray) else [axes]
        
        for idx, col in enumerate(numeric_cols):
            if idx >= len(axes):
                break
                
            ax = axes[idx]
            data = self.analyzer.df[col].dropna()
            
            if len(data) == 0:
                ax.text(0.5, 0.5, 'No Data', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(col, fontsize=10)
                continue
            
            # Create boxplot
            bp = ax.boxplot(data, vert=True, patch_artist=True,
                          boxprops=dict(facecolor=self.colors['info'], alpha=0.7),
                          medianprops=dict(color=self.colors['critical'], linewidth=2),
                          whiskerprops=dict(color=self.colors['warning'], linewidth=1.5),
                          capprops=dict(color=self.colors['warning'], linewidth=1.5),
                          flierprops=dict(marker='o', color=self.colors['critical'], 
                                         markersize=4, alpha=0.5))
            
            # Calculate and display outlier count
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = data[(data < lower_bound) | (data > upper_bound)]
            outlier_count = len(outliers)
            
            ax.set_title(f'{col}\nOutliers: {outlier_count} ({outlier_count/len(data)*100:.1f}%)', 
                        fontsize=10)
            ax.set_ylabel('Value')
            ax.set_xticks([])
            
            # Add statistical annotations
            stats_text = f'Q1: {Q1:.2f}\nQ3: {Q3:.2f}\nIQR: {IQR:.2f}'
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
                   fontsize=8, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Hide unused subplots
        for idx in range(len(numeric_cols), len(axes)):
            axes[idx].axis('off')
        
        plt.suptitle(f'Outlier Detection - {self.analyzer.name}', fontsize=14, y=1.02)
        plt.tight_layout()
        
        self.figures['outlier_detection'] = fig
        return fig
    
    def create_correlation_heatmap(self, figsize: Tuple = None) -> plt.Figure:
        """
        Create correlation heatmap for numeric columns.
        
        Parameters
        ----------
        figsize : tuple, optional
            Figure size (width, height)
            
        Returns
        -------
        matplotlib.figure.Figure
            The generated figure
        """
        numeric_cols = self.analyzer.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'Insufficient numeric columns for correlation analysis', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Correlation Heatmap - {self.analyzer.name}', fontsize=14)
            plt.tight_layout()
            return fig
        
        if figsize is None:
            figsize = (10, 8)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Calculate correlation matrix
        corr_matrix = self.analyzer.df[numeric_cols].corr()
        
        # Create heatmap
        sns.heatmap(corr_matrix, 
                   annot=True,
                   fmt='.2f',
                   cmap=VISUAL_CONFIG['correlation_cmap'],
                   center=0,
                   square=True,
                   linewidths=0.5,
                   cbar_kws={'shrink': 0.8, 'label': 'Correlation Coefficient'},
                   ax=ax)
        
        ax.set_title(f'Feature Correlations - {self.analyzer.name}', fontsize=14, pad=20)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        
        self.figures['correlation_heatmap'] = fig
        return fig
    
    def create_categorical_analysis(self, columns: List[str] = None,
                                   figsize: Tuple = None) -> plt.Figure:
        """
        Create bar plots for categorical column analysis.
        
        Parameters
        ----------
        columns : list of str, optional
            Specific columns to plot. If None, plots all categorical columns.
        figsize : tuple, optional
            Figure size (width, height)
            
        Returns
        -------
        matplotlib.figure.Figure
            The generated figure
        """
        if columns is None:
            cat_cols = self.analyzer.df.select_dtypes(include=['object', 'category']).columns.tolist()
        else:
            cat_cols = [col for col in columns if col in self.analyzer.df.columns]
        
        if not cat_cols:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'No Categorical Columns Found', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Categorical Analysis - {self.analyzer.name}', fontsize=14)
            plt.tight_layout()
            return fig
        
        # Determine grid layout
        n_cols = min(2, len(cat_cols))
        n_rows = (len(cat_cols) + n_cols - 1) // n_cols
        
        if figsize is None:
            figsize = (8 * n_cols, 6 * n_rows)
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten() if isinstance(axes, np.ndarray) else [axes]
        
        for idx, col in enumerate(cat_cols):
            if idx >= len(axes):
                break
                
            ax = axes[idx]
            data = self.analyzer.df[col].dropna()
            
            if len(data) == 0:
                ax.text(0.5, 0.5, 'No Data', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(col, fontsize=10)
                continue
            
            # Get value counts
            value_counts = data.value_counts()
            
            # Limit to top categories for readability
            max_categories = 15
            if len(value_counts) > max_categories:
                top_values = value_counts.head(max_categories - 1)
                other_count = value_counts.tail(len(value_counts) - max_categories + 1).sum()
                if other_count > 0:
                    top_values = pd.concat([top_values, pd.Series([other_count], index=['Other'])])
                value_counts = top_values
            
            # Create bar plot
            bars = ax.bar(range(len(value_counts)), value_counts.values,
                         color=self.colors['info'], alpha=0.8, edgecolor='white', linewidth=0.5)
            
            ax.set_title(f'{col}\n(Unique: {data.nunique()})', fontsize=10)
            ax.set_xlabel('Category')
            ax.set_ylabel('Count')
            
            # Set x-ticks
            ax.set_xticks(range(len(value_counts)))
            ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{int(height)}', ha='center', va='bottom', fontsize=8)
            
            # Add percentage annotations
            total = len(data)
            for i, (category, count) in enumerate(value_counts.items()):
                percentage = count / total * 100
                ax.text(i, count + total * 0.01, f'{percentage:.1f}%',
                       ha='center', va='bottom', fontsize=8, color='black')
        
        # Hide unused subplots
        for idx in range(len(cat_cols), len(axes)):
            axes[idx].axis('off')
        
        plt.suptitle(f'Categorical Analysis - {self.analyzer.name}', fontsize=14, y=1.02)
        plt.tight_layout()
        
        self.figures['categorical_analysis'] = fig
        return fig
    
    def create_comprehensive_report(self, save_path: str = None) -> Dict[str, plt.Figure]:
        """
        Create all visualizations and optionally save them.
        
        Parameters
        ----------
        save_path : str, optional
            Directory path to save figures
            
        Returns
        -------
        dict
            Dictionary of all generated figures
        """
        print(f"Generating comprehensive visual report for: {self.analyzer.name}")
        
        # Generate all visualizations
        figures = {}
        
        figures['missing_matrix'] = self.create_missing_values_matrix()
        figures['issues_summary'] = self.create_issues_summary_chart()
        figures['missing_distribution'] = self.create_missing_values_distribution()
        figures['numeric_distributions'] = self.create_numeric_distributions()
        figures['outlier_detection'] = self.create_outlier_detection_plot()
        figures['correlation_heatmap'] = self.create_correlation_heatmap()
        figures['categorical_analysis'] = self.create_categorical_analysis()
        
        # Save figures if path provided
        if save_path:
            import os
            os.makedirs(save_path, exist_ok=True)
            
            for name, fig in figures.items():
                filename = f"{save_path}/{self.analyzer.name.replace(' ', '_')}_{name}.png"
                fig.savefig(filename, dpi=VISUAL_CONFIG['dpi'], bbox_inches='tight')
                print(f"  Saved: {filename}")
        
        return figures