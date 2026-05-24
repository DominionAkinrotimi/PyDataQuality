import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def draw_architecture():
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.axis('off')
    
    # Layer definitions
    layers = [
        {
            "title": "INGESTION LAYER",
            "items": [
                "CLI Auto-Loader (CSV/Excel/JSON/Parquet)",
                "API Wrappers: analyze_dataframe(), quick_quality_check()"
            ]
        },
        {
            "title": "SAMPLING ENGINE",
            "items": [
                "sample_dataframe() — In-Memory Stratified/Random Sampler",
                "sample_large_dataset() — Chunk-Based File Sampler (OOM-Safe)"
            ]
        },
        {
            "title": "CORE PROFILING KERNEL",
            "items": [
                "DataQualityAnalyzer — Type-dispatched column audits",
                "QualityIssue Registry — Structured severity issue objects",
                "ColumnStats Registry — Per-column statistical summaries"
            ]
        },
        {
            "title": "DRIFT & DECISION ENGINE",
            "items": [
                "DataQualityComparator — Reference vs. Current comparison",
                "PSI Engine — Adaptive binning, information divergence",
                "KS Engine — ECDF comparison, SciPy or pure-NumPy backend"
            ]
        },
        {
            "title": "PRESENTATION LAYER",
            "items": [
                "HTML Dashboards — 3 themes: professional, creative, simple",
                "Matplotlib Visuals — Missing heatmaps, outlier boxplots",
                "JSON / Text Report Generators",
                "AI Remediation Prompt Generator (LLM bridge)"
            ]
        }
    ]

    box_width = 0.8
    box_height = 0.15
    start_y = 0.9
    spacing = 0.18

    # Draw boxes
    for i, layer in enumerate(layers):
        y = start_y - i * spacing
        
        # Adjust height based on number of items
        num_items = len(layer["items"])
        current_box_height = box_height + (num_items - 2) * 0.02
        y_adjusted = y - (current_box_height - box_height)/2
        
        # Draw box
        rect = patches.FancyBboxPatch(
            (0.1, y_adjusted - current_box_height), 
            box_width, current_box_height,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            edgecolor='black',
            facecolor='#f8f9fa',  # Off-white for B&W
            linewidth=1.5,
            zorder=2
        )
        ax.add_patch(rect)
        
        # Add Title
        title_y = y_adjusted - 0.03
        ax.text(0.5, title_y, layer["title"], 
                ha='center', va='center', fontsize=12, fontweight='bold', 
                bbox=dict(facecolor='#e9ecef', edgecolor='black', boxstyle='round,pad=0.3'))
        
        # Add Items
        item_y = title_y - 0.04
        for item in layer["items"]:
            ax.text(0.15, item_y, f"• {item}", ha='left', va='center', fontsize=10, family='monospace')
            item_y -= 0.03
            
        # Draw arrow to next layer
        if i < len(layers) - 1:
            next_y = start_y - (i + 1) * spacing
            ax.annotate('', 
                        xy=(0.5, next_y), 
                        xytext=(0.5, y_adjusted - current_box_height),
                        arrowprops=dict(facecolor='black', shrink=0.05, width=2, headwidth=8, headlength=10),
                        zorder=1)

    plt.title("PyDataQuality: Architecture Stack", fontweight='bold', fontsize=14, y=0.98)
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(output_dir, 'fig_architecture_bw.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {out_path}")

if __name__ == '__main__':
    draw_architecture()
