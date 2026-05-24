import time
import os
import sys
import json
import psutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add parent directory to path to import pydataquality
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq
from ydata_profiling import ProfileReport

def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def generate_benchmark_data(rows):
    """Generate synthetic dataset for testing."""
    np.random.seed(42)
    data = {
        'id': range(rows),
        'age': np.random.choice([np.nan, 25, 30, 35, 120, -5], rows, p=[0.05, 0.45, 0.2, 0.2, 0.05, 0.05]),
        'salary': np.random.normal(50000, 15000, rows),
        'category': np.random.choice(['A', 'B', 'C', 'D', 'a', 'b', 'A '], rows),
        'date_registered': pd.date_range('2020-01-01', periods=rows, freq='h'),
        'flag': np.random.choice([True, False], rows)
    }
    # Inject missing values
    df = pd.DataFrame(data)
    df.loc[df['salary'] < 30000, 'salary'] = np.nan
    return df

def run_experiment():
    print("Executing rigorous scaling benchmarks...")
    scales = [1000, 10000, 50000, 100000]
    
    results = {
        'scales': scales,
        'pandas_describe': {'time': [], 'memory': []},
        'pydataquality_full': {'time': [], 'memory': []},
        'pydataquality_sampled': {'time': [], 'memory': []},
        'ydata_profiling': {'time': [], 'memory': []}
    }
    
    for size in scales:
        print(f"\n--- Testing scale size: {size:,} rows ---")
        df = generate_benchmark_data(size)
        
        # 1. Base Pandas describe()
        print("Running pandas.describe()...")
        time.sleep(0.5) # allow cooldown
        mem_start = get_memory_usage()
        t_start = time.time()
        
        desc = df.describe(include='all')
        
        t_end = time.time()
        mem_end = get_memory_usage()
        results['pandas_describe']['time'].append(t_end - t_start)
        results['pandas_describe']['memory'].append(max(0.0, mem_end - mem_start))
        
        # 2. PyDataQuality with 1000-row sampling
        print("Running pydataquality (sampled)...")
        time.sleep(0.5)
        mem_start = get_memory_usage()
        t_start = time.time()
        
        # Sample to 1000 rows using utility
        sampled_df = pdq.sample_dataframe(df, n_samples=1000)
        analyzer_samp = pdq.analyze_dataframe(sampled_df, name="Sampled")
        pdq.generate_report(analyzer_samp, format='html')
        
        t_end = time.time()
        mem_end = get_memory_usage()
        results['pydataquality_sampled']['time'].append(t_end - t_start)
        results['pydataquality_sampled']['memory'].append(max(0.0, mem_end - mem_start))
        
        # 3. PyDataQuality full analysis
        print("Running pydataquality (full dataset)...")
        time.sleep(0.5)
        mem_start = get_memory_usage()
        t_start = time.time()
        
        analyzer_full = pdq.analyze_dataframe(df, name="Full")
        pdq.generate_report(analyzer_full, format='html')
        
        t_end = time.time()
        mem_end = get_memory_usage()
        results['pydataquality_full']['time'].append(t_end - t_start)
        results['pydataquality_full']['memory'].append(max(0.0, mem_end - mem_start))
        
        # 4. YData-Profiling
        print("Running ydata-profiling...")
        time.sleep(0.5)
        mem_start = get_memory_usage()
        t_start = time.time()
        
        profile = ProfileReport(df, minimal=True, progress_bar=False)
        profile.to_html()
        
        t_end = time.time()
        mem_end = get_memory_usage()
        results['ydata_profiling']['time'].append(t_end - t_start)
        results['ydata_profiling']['memory'].append(max(0.0, mem_end - mem_start))
        
    # Write raw outputs honestly
    output_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(output_dir, 'benchmark_results.json'), 'w') as f:
        json.dump(results, f, indent=2)
        
    print("\nBenchmark completed successfully. Generating figures...")
    generate_plots(results, scales, output_dir)

def generate_plots(results, scales, output_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Execution Time Plot
    ax1.plot(scales, results['pandas_describe']['time'], marker='o', label='Pandas describe()', linewidth=1.5, color='#7f8c8d')
    ax1.plot(scales, results['pydataquality_sampled']['time'], marker='s', label='PyDataQuality (Sampled)', linewidth=2.0, color='#2ecc71')
    ax1.plot(scales, results['pydataquality_full']['time'], marker='^', label='PyDataQuality (Full)', linewidth=2.0, color='#3498db')
    ax1.plot(scales, results['ydata_profiling']['time'], marker='x', label='YData-Profiling (Minimal)', linewidth=2.0, color='#e74c3c')
    
    ax1.set_title('Execution Time Complexity', fontsize=12, fontweight='bold', pad=15)
    ax1.set_xlabel('Dataset Size (Rows)', fontsize=10)
    ax1.set_ylabel('Time (Seconds)', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(fontsize=9)
    
    # Peak Memory Plot
    ax2.plot(scales, results['pandas_describe']['memory'], marker='o', label='Pandas describe()', linewidth=1.5, color='#7f8c8d')
    ax2.plot(scales, results['pydataquality_sampled']['memory'], marker='s', label='PyDataQuality (Sampled)', linewidth=2.0, color='#2ecc71')
    ax2.plot(scales, results['pydataquality_full']['memory'], marker='^', label='PyDataQuality (Full)', linewidth=2.0, color='#3498db')
    ax2.plot(scales, results['ydata_profiling']['memory'], marker='x', label='YData-Profiling (Minimal)', linewidth=2.0, color='#e74c3c')
    
    ax2.set_title('Incremental Peak Memory Overhead', fontsize=12, fontweight='bold', pad=15)
    ax2.set_xlabel('Dataset Size (Rows)', fontsize=10)
    ax2.set_ylabel('Memory Usage Delta (MB)', fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(fontsize=9)
    
    plt.suptitle('Performance Benchmarking: PyDataQuality vs Baselines', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    plot_path = os.path.join(output_dir, 'benchmark_performance.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Benchmark chart saved to: {plot_path}")

if __name__ == '__main__':
    run_experiment()
