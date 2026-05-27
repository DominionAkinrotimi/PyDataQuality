import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def draw_ge_workflow():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis('off')
    
    # Layer definitions
    boxes = [
        {"id": "datasource", "title": "Data Context / Source", "subtitle": "(YAML Config)", "x": 0.1, "y": 0.7, "w": 0.35, "h": 0.15},
        {"id": "expectations", "title": "Expectation Suite", "subtitle": "(Declarative JSON/YAML)", "x": 0.55, "y": 0.7, "w": 0.35, "h": 0.15},
        {"id": "checkpoint", "title": "Checkpoint", "subtitle": "(YAML Execution Config)", "x": 0.325, "y": 0.4, "w": 0.35, "h": 0.15},
        {"id": "validation", "title": "Validation Engine", "subtitle": "(Execution)", "x": 0.325, "y": 0.1, "w": 0.35, "h": 0.15},
    ]

    for b in boxes:
        rect = patches.FancyBboxPatch(
            (b["x"], b["y"]), b["w"], b["h"],
            boxstyle="round,pad=0.02,rounding_size=0.02",
            edgecolor='black',
            facecolor='#f8f9fa',
            linewidth=1.5,
            zorder=2
        )
        ax.add_patch(rect)
        
        # Add Title
        ax.text(b["x"] + b["w"]/2, b["y"] + b["h"]/2 + 0.02, b["title"], 
                ha='center', va='center', fontsize=12, fontweight='bold')
        # Add Subtitle
        ax.text(b["x"] + b["w"]/2, b["y"] + b["h"]/2 - 0.03, b["subtitle"], 
                ha='center', va='center', fontsize=10, style='italic')

    # Draw arrows
    # Datasource -> Checkpoint
    ax.annotate('', xy=(0.4, 0.55), xytext=(0.275, 0.7),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8), zorder=1)
    
    # Expectations -> Checkpoint
    ax.annotate('', xy=(0.6, 0.55), xytext=(0.725, 0.7),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8), zorder=1)
                
    # Checkpoint -> Validation
    ax.annotate('', xy=(0.5, 0.25), xytext=(0.5, 0.4),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8), zorder=1)
                
    # Outputs from Validation
    ax.annotate('', xy=(0.2, 0.175), xytext=(0.325, 0.175),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8), zorder=1)
    ax.text(0.1, 0.175, "Data Docs\n(HTML)", ha='center', va='center', fontsize=10, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.3'))

    ax.annotate('', xy=(0.8, 0.175), xytext=(0.675, 0.175),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8), zorder=1)
    ax.text(0.9, 0.175, "Validation\nResults", ha='center', va='center', fontsize=10, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.3'))

    # Configuration bounding box to emphasize overhead
    rect_config = patches.Rectangle((0.05, 0.35), 0.9, 0.55, linewidth=1.5, edgecolor='black', linestyle='--', facecolor='none', zorder=0)
    ax.add_patch(rect_config)
    ax.text(0.08, 0.86, "Configuration Overhead (Heavy)", fontsize=11, fontweight='bold', fontstyle='italic')

    plt.title("Great Expectations: Configuration vs. Computation Workflow", fontweight='bold', fontsize=14, y=0.95)
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(output_dir, 'fig_great_expectations_bw.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {out_path}")

if __name__ == '__main__':
    draw_ge_workflow()
