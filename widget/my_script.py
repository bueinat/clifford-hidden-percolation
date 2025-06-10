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
    
    plots = []
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
            # with open(scaled_svg, 'rb') as f:
            #     svg_data = f.read()
            #     svg_base64 = base64.b64encode(svg_data).decode('utf-8')
            #     plots.append((svg_base64, name))  # Store SVG data and name for display
            
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
        if cleanup_intermediates:
            try:
                os.remove(default_svg)
            except OSError:
                pass
    
    return plots


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
    # print("מבצע בדיקות מקדימות...")

    # # הדמיית תהליך חישוב
    # if r == 0: # This case is handled in app.py, but good for robust script
    #     print("אזהרה: r הוא 0. החישוב עלול להיות בעייתי.")
    
    # # חישוב לדוגמה
    # try:
    #     final_result = p * r + (p / r)
    # except ZeroDivisionError:
    #     print("שגיאה במהלך החישוב: חלוקה באפס!")
    #     final_result = float('nan') # Not a number
        
    # print(f"תוצאה זמנית: {p * r:.2f}")
    # print(f"תוצאה נוספת: {p / r:.2f}")
    stats = calculate_result(N, p, r)

    # יצירת גרפים בפורמט SVG
    svg_plots = []
    num_demo_plots = 3 # מספר הגרפים שיוצגו בסלייד-שואו

    print(f"יוצר {num_demo_plots} גרפים לדוגמה...")
    for i in range(num_demo_plots):
        print(f"יוצר גרף מספר {i+1}...")
        
        # יצירת נתונים לגרף
        x = np.linspace(0, 10, 100)
        y = np.sin(x * (i + 1) / 2) * (p / r) + np.random.normal(0, 0.5, 100)
        
        # יצירת אובייקט גרף של Matplotlib
        fig, ax = plt.subplots(figsize=(7, 5)) # גודל גרף מותאם
        ax.plot(x, y, label=f'סדרה {i+1}')
        ax.set_title(f"גרף תוצאה {i+1} (p={p:.1f}, r={r:.1f})", fontsize=14)
        ax.set_xlabel("ציר X", fontsize=12)
        ax.set_ylabel("ציר Y", fontsize=12)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout() # התאמת הפריסה למניעת חיתוך כותרות

        # שמירת הגרף כמחרוזת SVG
        img_buffer = io.StringIO()
        fig.savefig(img_buffer, format='svg')
        svg_plots.append(img_buffer.getvalue())
        
        plt.close(fig) # סגירת הגרף לשחרור זיכרון (חשוב!)
        
    svg_plots = create_plots(stats)
    final_result = 100

    # print(f"** חישוב וייצור גרפים הסתיימו. תוצאה סופית: {final_result:.2f} **")

    # שחזור sys.stdout למצב רגיל
    sys.stdout = sys.__stdout__
    # קבלת כל הפלט שנלכד
    logs = captured_output.getvalue()

    return logs, svg_plots, final_result


import wcore as core

# def calculate_result(p, r):
#     """
#     פונקציה לדוגמה שמבצעת חישוב כלשהו על בסיס הפרמטרים p ו-r.
#     במציאות, זה יהיה הקוד הפייתון שלך.
#     """
#     result = p * r + (p / r)
#     return result



def main():
    # כאן ירוץ הקוד שלך כשהוא נקרא ישירות
    # במקרה של streamlit, הוא לא ירוץ ישירות מכאן, אלא מתוך הפונקציה באפליקציה.
    pass

if __name__ == "__main__":
    main()