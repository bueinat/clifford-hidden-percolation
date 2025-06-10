# my_script.py

# my_script.py
import io
import sys
from venv import create
import matplotlib.pyplot as plt
import numpy as np
import pyzx as zx
import os
import base64
import wcore as core


def calculate_result(N, p, r):
    t_factor, periodic, quiet = 4, False, True
    q, u = 0.5, 0
    string_circuit = core.sample_string_circuit(
        N, t_factor, periodic=periodic, p=p, q=q, r=r, u=u)
    g, qubits = core.sample_circuit(
            N, t_factor, string_circuit=string_circuit, apply_state=False, periodic=periodic)
    stats = core.simplified_modified.Stats()
    core.simplify_circuit(g, quiet, core.full_reduce, stats=stats)
    return stats

def create_plots(stats, figsize=(20, 5), cleanup_intermediates=True):
    """
    Generate a list of base64-encoded SVGs from processed Matplotlib plots.
    
    Args:
        stats: Object containing freeze_graph (dict or iterable of graph objects).
        path: Directory to save SVG files.
        figsize: Tuple of (width, height) for the figure size.
        cleanup_intermediates: If True, delete intermediate SVG files after processing.
    
    Returns:
        List of base64-encoded SVG strings and their names.
    """
    # Ensure output directory exists
    # os.makedirs(path, exist_ok=True)
    
    plots, names = [], []
    graph_keys = list(stats.freeze_graph) if isinstance(stats.freeze_graph, dict) else stats.freeze_graph
    
    for key in graph_keys:
        # print(key)
        try:
            # Generate plot name from key (assuming key is a tuple like (x, y))
            name = f"{key[0]}_{key[1]}" if isinstance(key, tuple) else str(key)
            
            # Generate Matplotlib figure
            fig = zx.draw_matplotlib(
                stats.freeze_graph[key] if isinstance(stats.freeze_graph, dict) else key,
                h_edge_draw='box',
                figsize=figsize
            )
            
            # Save initial SVG
            initial_svg = f"{name}.svg"
            fig.savefig(initial_svg, format='svg', transparent=True, bbox_inches='tight')
            plt.close(fig)  # Close figure to free memory
            
            # Process SVG
            processed_svg = f"{name}_output.svg"
            scaled_svg = f"{name}_output_scaled.svg"
            core.replace_paths_with_shapes(initial_svg, processed_svg)
            core.scale_svg(processed_svg, scaled_svg, 0.4, 0.9)
            
            # Read the final SVG and encode to base64
            with open(scaled_svg, "r", encoding="utf-8") as f:
                svg_content = f.read()
                plots.append(svg_content)
                names.append(name)
            
            # Clean up intermediate files if requested
            if cleanup_intermediates:
                for svg_file in [initial_svg, processed_svg, scaled_svg]:
                    try:
                        os.remove(svg_file)
                    except OSError:
                        pass
                        
        except Exception as e:
            print(f"Error processing plot for key {key}: {e}")
            continue
    
    # Return a default SVG if no plots were generated
    if not plots:
        print("No plots generated. Creating a default SVG.")
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No graphs available", ha='center', va='center')
        ax.set_title("Default Plot")
        default_svg = f"default.svg"
        fig.savefig(default_svg, format='svg', transparent=True, bbox_inches='tight')
        plt.close(fig)
        with open(default_svg, 'rb') as f:
            svg_data = f.read()
            svg_base64 = base64.b64encode(svg_data).decode('utf-8')
            plots.append((svg_base64, "default"))
            names.append('default')
        if cleanup_intermediates:
            try:
                os.remove(default_svg)
            except OSError:
                pass
    
    return plots, names


def perform_calculation_and_generate_plots(N, p, r):
    """
    מבצע חישוב כלשהו על בסיס p ו-r, מדפיס הודעות תהליך,
    ומייצר סדרה של גרפים בפורמט SVG.
    """
    # יצירת אובייקט StringIO ללכידת פלטי הדפסה
    captured_output = io.StringIO()
    # הפניית sys.stdout לאובייקט שלנו
    sys.stdout = captured_output

    print(f"** מתחיל חישוב עבור N={N}, p={p:.2f} ו-r={r:.2f} **")

    stats = calculate_result(N, p, r)
    svg_plots, svg_names = create_plots(stats)
    final_result = 100


    # שחזור sys.stdout למצב רגיל
    sys.stdout = sys.__stdout__
    # קבלת כל הפלט שנלכד
    logs = captured_output.getvalue()

    return logs, svg_plots, svg_names, final_result
