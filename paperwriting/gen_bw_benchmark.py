"""Regenerate benchmark performance chart in black and white for journal submission."""
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'legend.fontsize': 10,
    'figure.dpi': 200,
})

out_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(out_dir, 'benchmark_results.json')) as f:
    results = json.load(f)

scales = results['scales']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

styles = [
    ('pandas_describe',       'Pandas describe()',           'o',  '-',  '#000000', 1.5),
    ('pydataquality_sampled', 'PyDataQuality (Sampled)',     's',  '--', '#333333', 2.0),
    ('pydataquality_full',    'PyDataQuality (Full)',        '^',  '-',  '#666666', 2.0),
    ('ydata_profiling',       'YData-Profiling (Minimal)',   'x',  ':', '#999999', 2.0),
    ('pdq_drift',             'PyDataQuality (Drift)',       'v',  '-.', '#555555', 1.5),
    ('evidently_drift',       'Evidently (DataDriftPreset)', 'D',  '-',  '#111111', 1.5)
]

for key, label, marker, ls, color, lw in styles:
    if key not in results or len(results[key]['time']) == 0:
        continue
        
    ax1.errorbar(scales, results[key]['time'], yerr=results[key]['time_std'], 
                 marker=marker, linestyle=ls, color=color, linewidth=lw, label=label, markersize=7, capsize=3)
    ax2.errorbar(scales, results[key]['memory'], yerr=results[key]['memory_std'], 
                 marker=marker, linestyle=ls, color=color, linewidth=lw, label=label, markersize=7, capsize=3)

for ax, title, ylabel in [
    (ax1, 'Execution Time Complexity', 'Execution Time (Seconds)'),
    (ax2, 'Incremental Peak Memory Overhead', 'Memory Usage Delta (MB)'),
]:
    ax.set_title(title, fontweight='bold', pad=12)
    ax.set_xlabel('Dataset Size (Rows)')
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle=':', alpha=0.5, color='gray')
    ax.legend(framealpha=0.9, edgecolor='black', fontsize=9)
    ax.set_facecolor('white')
    ax.spines[['top', 'right']].set_visible(False)

fig.suptitle('Figure 8: Performance Benchmarking — PyDataQuality vs. Baseline Tools',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()

path = os.path.join(out_dir, 'benchmark_performance.png')
plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Saved: {path}")
