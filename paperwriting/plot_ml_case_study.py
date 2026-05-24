import json
import os
import matplotlib.pyplot as plt
import numpy as np

def plot_results():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, 'ml_case_study_results.json')
    
    with open(json_path, 'r') as f:
        results = json.load(f)
        
    synthetic = results['synthetic']
    real_world = results['real_world']
    
    pipelines = ['Baseline\n(Clean)', 'Pipeline A\n(Unmitigated)', 'Pipeline B\n(PyDataQuality)']
    
    f1_synthetic = [
        synthetic['baseline']['f1'],
        synthetic['pipeline_a']['f1'],
        synthetic['pipeline_b']['f1']
    ]
    
    r2_real = [
        real_world['baseline']['r2'],
        real_world['pipeline_a']['r2'],
        real_world['pipeline_b']['r2']
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    # Pattern and grayscale colors for Black & White print constraint
    patterns = ['/', '\\', 'x']
    colors = ['#cccccc', '#888888', '#444444']

    # Synthetic Dataset Plot (Classification -> F1 Score)
    bars1 = ax1.bar(pipelines, f1_synthetic, color=colors, edgecolor='black', hatch=patterns)
    ax1.set_title('Synthetic Loan Dataset (F1 Score)', fontweight='bold')
    ax1.set_ylabel('F1 Score (Higher is Better)')
    ax1.set_ylim(0, 1.0)
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.02, round(yval, 3), ha='center', va='bottom', fontweight='bold')

    # California Housing Dataset Plot (Regression -> R^2 Score)
    min_r2 = min(r2_real)
    min_ylim = min(-1.5, min_r2 - 0.2)
    bars2 = ax2.bar(pipelines, r2_real, color=colors, edgecolor='black', hatch=patterns)
    ax2.set_title('California Housing Dataset ($R^2$ Score)', fontweight='bold')
    ax2.set_ylabel('$R^2$ Score (Higher is Better)')
    ax2.set_ylim(min_ylim, 1.1)
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    for bar in bars2:
        yval = bar.get_height()
        y_text = yval + 0.05 if yval > 0 else yval - 0.15
        ax2.text(bar.get_x() + bar.get_width()/2, y_text, round(yval, 3), ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    out_path = os.path.join(output_dir, 'fig_mlops_dual_bw.png')
    plt.savefig(out_path, dpi=300)
    print(f"Saved plot to {out_path}")

if __name__ == '__main__':
    plot_results()
