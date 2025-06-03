import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import base64
import os

import pyzx as zx
import wcore as core

from tqdm.notebook import tqdm
import matplotlib.pyplot as plt

def create_plots(stats, path="plots/diagrams", figsize=(20, 5), cleanup_intermediates=True):
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
    os.makedirs(path, exist_ok=True)
    
    plots = []
    graph_keys = list(stats.freeze_graph) if isinstance(stats.freeze_graph, dict) else stats.freeze_graph
    
    for key in tqdm(graph_keys):
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
            initial_svg = f"{path}/{name}.svg"
            fig.savefig(initial_svg, format='svg', transparent=True, bbox_inches='tight')
            plt.close(fig)  # Close figure to free memory
            
            # Process SVG
            processed_svg = f"{path}/{name}_output.svg"
            scaled_svg = f"{path}/{name}_output_scaled.svg"
            core.replace_paths_with_shapes(initial_svg, processed_svg)
            core.scale_svg(processed_svg, scaled_svg, 0.4, 0.9)
            
            # Read the final SVG and encode to base64
            with open(scaled_svg, 'rb') as f:
                svg_data = f.read()
                svg_base64 = base64.b64encode(svg_data).decode('utf-8')
                plots.append((svg_base64, name))  # Store SVG data and name for display
            
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
        default_svg = f"{path}/default.svg"
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

def generate_title(plots, index):
        return f"{plots[index][1].split('_')[1]} rule ({index + 1} of {len(plots)})"

def create_slideshow(stats, path="plots/diagrams", figsize=(10, 5), cleanup_intermediates=False):
    plots = create_plots(stats, path, figsize, cleanup_intermediates=cleanup_intermediates)
    current_index = [0]

    # Title widget
    title = widgets.HTML(
        value=f"<h4 style='text-align:center; margin:10px;'>{generate_title(plots, 0)}</h4>",
        layout={'width': '100%'}
    )

    # Image widget (adjusted to prevent cutoff)
    img_widget = widgets.Image(
        value=base64.b64decode(plots[0][0]),
        format='svg+xml',
        layout={'width': '800px', 'max_width': '100%', 'height': 'auto', 'margin': 'auto', 'border': '1px solid #ccc',}
    )

    # Arrow buttons
    left_button = widgets.Button(
        description='←',
        layout={'width': '50px', 'height': '50px', 'margin': '0 10px'},
        style={'button_color': '#f0f0f0', 'font_weight': 'bold'},
        tooltip='Previous Plot'
    )
    right_button = widgets.Button(
        description='→',
        layout={'width': '50px', 'height': '50px', 'margin': '0 10px'},
        style={'button_color': '#f0f0f0', 'font_weight': 'bold'},
        tooltip='Next Plot'
    )

    # Image and arrows in a horizontal box
    image_box = widgets.HBox(
        [left_button, img_widget, right_button],
        layout={'justify_content': 'center', 'align_items': 'center', 'overflow': 'hidden'}
    )

    # Persistent indicator dots
    dots = [
        widgets.HTML(
            value=f"<span style='font-size:20px; color:{'#333' if i == 0 else '#ccc'}'>●</span>",
            layout={'margin': '0 5px'}
        ) for i in range(len(plots))
    ]
    indicator_box = widgets.HBox(
        dots,
        layout={'justify_content': 'center', 'margin': '10px 0'}
    )

    # Main layout
    layout = widgets.VBox(
        [title, image_box, indicator_box],
        layout={
            'border': '1px solid #ccc',
            'padding': '10px',
            'width': '900px',
            'max_width': '100%',
            'margin': '10px',
            'background_color': '#fff',
            'box_shadow': '0 2px 8px rgba(0, 0, 0, 0.1)',
            'overflow': 'hidden'
        }
    )

    # Button click handlers
    def update_dots():
        for i, dot in enumerate(dots):
            dot.value = f"<span style='font-size:20px; color:{'#333' if i == current_index[0] else '#ccc'}'>●</span>"

    def on_left_click(b):
        current_index[0] = (current_index[0] - 1) % len(plots)
        img_widget.value = base64.b64decode(plots[current_index[0]][0])
        title.value = f"<h4 style='text-align:center; margin:10px;'>{generate_title(plots, current_index[0])}</h4>"
        update_dots()

    def on_right_click(b):
        current_index[0] = (current_index[0] + 1) % len(plots)
        img_widget.value = base64.b64decode(plots[current_index[0]][0])
        title.value = f"<h4 style='text-align:center; margin:10px;'>{generate_title(plots, current_index[0])}</h4>"
        update_dots()
        
    
    left_button.on_click(on_left_click)
    right_button.on_click(on_right_click)

    return layout

def create_parameter_widget():
    # Parameter input widgets
    n_slider = widgets.IntSlider(
        value=12,
        min=4,
        step=2,
        max=50,
        description='N:',
        style={'description_width': 'initial'},
        layout={'width': '400px'}
    )
    t_factor_slider = widgets.FloatSlider(
        value=2.0,
        min=0.1,
        max=4.0,
        step=0.1,
        description='t_factor:',
        style={'description_width': 'initial'},
        layout={'width': '400px'}
    )
    p_slider = widgets.FloatSlider(
        value=0.25,
        min=0.0,
        max=1.0,
        step=0.05,
        description='p:',
        style={'description_width': 'initial'},
        layout={'width': '400px'}
    )
    r_slider = widgets.FloatSlider(
        value=0.2,
        min=0.0,
        max=1.0,
        step=0.05,
        description='r:',
        style={'description_width': 'initial'},
        layout={'width': '400px'}
    )

    # Run button
    run_button = widgets.Button(
        description='Run',
        button_style='success',
        tooltip='Run the circuit simulation',
        layout={'width': '100px', 'margin': '10px'}
    )

    # Parameter box
    param_box = widgets.VBox(
        [
            widgets.HTML("<h3 style='text-align:center;'>Parameters</h3>"),
            n_slider,
            t_factor_slider,
            p_slider,
            r_slider,
            run_button
        ],
        layout={
            'border': '1px solid #ccc',
            'padding': '10px',
            'width': '450px',
            'margin': '10px',
            'background_color': '#fff',
            'box_shadow': '0 2px 8px rgba(0, 0, 0, 0.1)',
            'overflow': 'hidden'
        }
    )

    # Output box
    out = widgets.Output(layout={'width': '100%', 'height': '200px', 'overflow_y': 'scroll'})
    out.add_class("output-wrap")
    output_box = widgets.VBox(
        [
            widgets.HTML("<h3 style='text-align:center;'>Output</h3>"),
            out
        ],
        layout={
            'border': '1px solid #ccc',
            'padding': '10px',
            'width': '450px',
            'margin': '10px',
            'background_color': '#fff',
            'box_shadow': '0 2px 8px rgba(0, 0, 0, 0.1)',
            'overflow': 'hidden'
        }
    )
    
    # Plot box (larger to accommodate slideshow)
    plot_box = widgets.VBox(
        [widgets.HTML("<h3 style='text-align:center;'>Plots</h3>")],
        layout={
            'border': '1px solid #ccc',
            'padding': '10px',
            'width': '950px',
            'max_width': '100%',
            'margin': '10px',
            'background_color': '#fff',
            'box_shadow': '0 2px 8px rgba(0, 0, 0, 0.1)',
            'overflow': 'auto'
        }
    )

    # Overall layout: Parameters and Output side-by-side, Plots below
    top_row = widgets.HBox(
        [param_box, output_box],
        layout={'justify_content': 'center', 'align_items': 'flex-start'}
    )
    main_layout = widgets.VBox(
        [top_row, plot_box],
        layout={'justify_content': 'center', 'align_items': 'center', 'padding': '10px'}
    )

    # Button click handler
    def on_run_click(b):
        output_widget = output_box.children[1]  # Output widget
        with output_widget:
            clear_output()
            display(widgets.HTML("<span style='color:olive; font-weight: bold;'>Computing...</span>"))
            try:
                # Get parameter values
                N = n_slider.value
                t_factor = t_factor_slider.value
                periodic = True
                p = p_slider.value
                # q = q_slider.value
                r = r_slider.value
                # u = u_slider.value
                q, u = 0.5, 0
                quiet = True

                # Run the computation
                with out:
                    display(widgets.HTML("<span style='color:olive; '>   generating a circuit...</span>"))
                    string_circuit = core.sample_string_circuit(
                        N, t_factor, periodic=periodic, p=p, q=q, r=r, u=u)
                    g, qubits = core.sample_circuit(
                        N, t_factor, string_circuit=string_circuit, apply_state=False, periodic=periodic)
                    display(widgets.HTML("<span style='color:olive; '>   simplifying...</span>"))
                    stats = core.simplified_modified.Stats()
                    core.simplify_circuit(g, quiet, core.full_reduce, stats=stats)

                # Update plot box
                display(widgets.HTML("<span style='color:olive; '>   generating plots...</span>"))
                slideshow = create_slideshow(stats, path="plots/diagrams", figsize=(10, 5), cleanup_intermediates=True)
                plot_box.children = [plot_box.children[0], slideshow]
                # clear_output()
                display(widgets.HTML("<span style='color:green; font-weight: bold;'>Computation completed successfully.</span>"))
            except Exception as e:
                # clear_output()
                display(HTML(f"<span style='color: red; font-weight: bold;'>Error: {str(e)}</span>"))

    run_button.on_click(on_run_click)

    return main_layout