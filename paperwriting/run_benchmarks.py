import time
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from memory_profiler import memory_usage

# Add parent directory to path to import pydataquality
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq
from ydata_profiling import ProfileReport

try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
    print("Warning: Evidently is not installed.")

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
    df = pd.DataFrame(data)
    df.loc[df['salary'] < 30000, 'salary'] = np.nan
    return df

def generate_drifted_data(df):
    """Generate a drifted version of the dataframe."""
    df_drift = df.copy()
    # Introduce severe drift in salary
    df_drift['salary'] = df_drift['salary'] - 20000
    return df_drift

def run_experiment():
    print("Executing rigorous scaling benchmarks (Profiling & Drift)...")
    scales = [1000, 10000, 50000, 100000]
    n_runs = 5
    
    results = {
        'scales': scales,
        'pandas_describe': {'time': [], 'time_std': [], 'memory': [], 'memory_std': []},
        'pydataquality_sampled': {'time': [], 'time_std': [], 'memory': [], 'memory_std': []},
        'pydataquality_full': {'time': [], 'time_std': [], 'memory': [], 'memory_std': []},
        'ydata_profiling': {'time': [], 'time_std': [], 'memory': [], 'memory_std': []},
        'evidently_drift': {'time': [], 'time_std': [], 'memory': [], 'memory_std': []},
        'pdq_drift': {'time': [], 'time_std': [], 'memory': [], 'memory_std': []}
    }
    
    for size in scales:
        print(f"\n--- Testing scale size: {size:,} rows ---")
        df_ref = generate_benchmark_data(size)
        df_curr = generate_drifted_data(df_ref)
        
        # Helper to run benchmarks
        def benchmark_func(func, *args, **kwargs):
            times = []
            mems = []
            for _ in range(n_runs):
                t0 = time.time()
                mem = memory_usage((func, args, kwargs), max_usage=True, retval=False)
                t1 = time.time()
                times.append(t1 - t0)
                # Subtract baseline memory (which is roughly memory_usage before func, but memory_usage runs it in a subprocess or current process)
                # Actually, memory_usage with max_usage=True returns the peak memory. We need incremental.
                # A simpler way for incremental peak:
                pass
            return times, mems
            
        # Let's use a simpler wrapper for memory_profiler that gets baseline first
        def measure(func, *args):
            t_list, m_list = [], []
            for _ in range(n_runs):
                base_mem = memory_usage(-1, interval=0.1, timeout=0.1)[0]
                t0 = time.time()
                mem_usage = memory_usage((func, args), max_usage=True, include_children=False)
                t1 = time.time()
                peak_mem = mem_usage[0] if isinstance(mem_usage, list) else mem_usage
                
                t_list.append(t1 - t0)
                m_list.append(max(0.0, peak_mem - base_mem))
                time.sleep(0.1)
            return np.mean(t_list), np.std(t_list), np.mean(m_list), np.std(m_list)

        def run_pandas(df): df.describe(include='all')
        def run_pdq_sampled(df): 
            sampled = pdq.sample_dataframe(df, n_samples=1000)
            a = pdq.analyze_dataframe(sampled)
            a.to_dict()
        def run_pdq_full(df): 
            a = pdq.analyze_dataframe(df)
            a.to_dict()
        def run_ydata(df): 
            ProfileReport(df, minimal=True, progress_bar=False).to_html()
            
        def run_evidently(ref, curr):
            report = Report(metrics=[DataDriftPreset()])
            report.run(reference_data=ref, current_data=curr)
            
        def run_pdq_drift(ref, curr):
            # Sample for drift detection (to keep it fast, PDQ way)
            r_samp = pdq.sample_dataframe(ref, 1000)
            c_samp = pdq.sample_dataframe(curr, 1000)
            a_ref = pdq.analyze_dataframe(r_samp)
            a_curr = pdq.analyze_dataframe(c_samp)
            pdq.compare_drift(a_ref, a_curr)

        print("1. Pandas describe()")
        t_m, t_s, m_m, m_s = measure(run_pandas, df_ref)
        results['pandas_describe']['time'].append(t_m); results['pandas_describe']['time_std'].append(t_s)
        results['pandas_describe']['memory'].append(m_m); results['pandas_describe']['memory_std'].append(m_s)
        
        print("2. PyDataQuality (Sampled)")
        t_m, t_s, m_m, m_s = measure(run_pdq_sampled, df_ref)
        results['pydataquality_sampled']['time'].append(t_m); results['pydataquality_sampled']['time_std'].append(t_s)
        results['pydataquality_sampled']['memory'].append(m_m); results['pydataquality_sampled']['memory_std'].append(m_s)
        
        print("3. PyDataQuality (Full)")
        t_m, t_s, m_m, m_s = measure(run_pdq_full, df_ref)
        results['pydataquality_full']['time'].append(t_m); results['pydataquality_full']['time_std'].append(t_s)
        results['pydataquality_full']['memory'].append(m_m); results['pydataquality_full']['memory_std'].append(m_s)
        
        print("4. YData-Profiling (Minimal)")
        t_m, t_s, m_m, m_s = measure(run_ydata, df_ref)
        results['ydata_profiling']['time'].append(t_m); results['ydata_profiling']['time_std'].append(t_s)
        results['ydata_profiling']['memory'].append(m_m); results['ydata_profiling']['memory_std'].append(m_s)

        print("5. PyDataQuality (Drift Detection)")
        t_m, t_s, m_m, m_s = measure(run_pdq_drift, df_ref, df_curr)
        results['pdq_drift']['time'].append(t_m); results['pdq_drift']['time_std'].append(t_s)
        results['pdq_drift']['memory'].append(m_m); results['pdq_drift']['memory_std'].append(m_s)
        
        if EVIDENTLY_AVAILABLE:
            print("6. Evidently AI (DataDriftPreset)")
            t_m, t_s, m_m, m_s = measure(run_evidently, df_ref, df_curr)
            results['evidently_drift']['time'].append(t_m); results['evidently_drift']['time_std'].append(t_s)
            results['evidently_drift']['memory'].append(m_m); results['evidently_drift']['memory_std'].append(m_s)

    # Write raw outputs
    output_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(output_dir, 'benchmark_results.json'), 'w') as f:
        json.dump(results, f, indent=2)
        
    print("\nBenchmark completed successfully.")

if __name__ == '__main__':
    run_experiment()
