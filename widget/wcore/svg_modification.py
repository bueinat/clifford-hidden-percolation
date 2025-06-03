import xml.etree.ElementTree as ET
import re
import numpy as np
from lxml import etree
import math


def clean_svg_string(s):
    """
    Cleans an SVG-like string by keeping only digits, decimal points, and spaces.
    Also removes any duplicate spaces and trims leading/trailing spaces.
    """
    # Retain only digits, decimal points, and spaces
    cleaned = re.sub(r"[^\d.\s]", "", s)
    # Replace multiple spaces or newline characters with a single space
    formatted = re.sub(r"\s+", " ", cleaned).strip()
    return np.array(formatted.split(' ')).astype(float)


def calculate_circle_radius_average(a):
    # Extract x and y coordinates from the input
    x_coords = np.array(a[::2])
    y_coords = np.array(a[1::2])

    # Calculate the approximate center as the mean of x and y coordinates
    x_center = np.mean(x_coords)
    y_center = np.mean(y_coords)

    # Compute distances from the center to each point
    distances = np.sqrt((x_coords - x_center)**2 + (y_coords - y_center)**2)

    # Calculate the radius as the mean distance
    radius = np.mean(distances)

    return x_center, y_center, radius


def classify_path(path_data):
    """
    Function to classify if a path is a circle or a line.
    Returns 'circle', 'line', or None.
    """
    # Replace this with your actual classification logic
    if 'C' in path_data:  # Example placeholder logic
        return "circle"
    elif 'z' in path_data:
        return "polygon"
    else:
        return "line"
    # return None


def generate_circle_properties(a):
    """
    Generate circle properties (cx, cy, r) from path data.
    """
    cx, cy, r = calculate_circle_radius_average(a)
    return {"cx": str(cx), "cy": str(cy), "r": str(r)}


def generate_line_properties(a):
    """
    Generate line properties (x1, y1, x2, y2) from path data.
    """
    x1, y1, x2, y2 = a
    return {"x1": str(x1), "y1": str(y1), "x2": str(x2), "y2": str(y2)}


def generate_rectangle_properties(a):
    """
    Generate rectangle properties  from path data.
    """
    xs, ys = a[::2], a[1::2]
    # Compute rectangle properties
    x = min(xs)
    y = min(ys)
    width = max(xs) - x
    height = max(ys) - y

    # Return the rectangle attributes
    return {"x": str(x), "y": str(y), "width": str(width), "height": str(height)}


def generate_polygon_properties(a):
    """
    Generate SVG-compatible polygon points, bounding box, and rotation angle
    from path data representing a tilted rectangle.

    Args:
        a (list or tuple): A list of 8 floats: [x1, y1, x2, y2, x3, y3, x4, y4]

    Returns:
        dict: {
            "points": str,         # SVG <polygon> 'points' string
            "x": str,              # bounding box x
            "y": str,              # bounding box y
            "width": str,          # bounding box width
            "height": str,         # bounding box height
            "rotation": float      # angle in degrees
        }
    """
    # if len(a) != 8:
    #     raise ValueError("Expected 8 values representing 4 (x, y) corner pairs")
    xs, ys = a[::2], a[1::2]

    # Get point list
    points = [(xs[i], ys[i]) for i in range(len(xs))]
    points_str = " ".join(f"{x},{y}" for x, y in points)

    # Bounding box
    xs, ys = a[::2], a[1::2]
    x_min = min(xs)
    y_min = min(ys)
    width = max(xs) - x_min
    height = max(ys) - y_min

    # Rotation angle from first side (p1 -> p2)
    x1, y1 = points[0]
    x2, y2 = points[1]
    dx = x2 - x1
    dy = y2 - y1
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)

    return {
        "points": points_str,
        # "x": str(x_min),
        # "y": str(y_min),
        # "width": str(width),
        # "height": str(height),
        # "rotation": angle_deg
    }


def generate_shape_properties(path_data, shape):
    a = clean_svg_string(path_data.attrib.get("d", ""))
    if shape == 'line':
        return generate_line_properties(a)
    if shape == 'circle':
        return generate_circle_properties(a)
    if shape == 'polygon':
        return generate_polygon_properties(a)
        # return generate_rectangle_properties(a)
    raise Exception("invalid shape")


def update_fill_attribute(style):

    style_dict = dict(item.split(":")
                      for item in style.split(";") if ":" in item)

    # Access the 'fill' property and update it
    original_fill = style_dict.get("fill", None)
    if original_fill != None:
        if '008000' in original_fill:
            style_dict["fill"] = '#d8f8d8'  # Update the fill color
        elif 'ff0000' in original_fill:
            style_dict['fill'] = '#e39191'

    # Reconstruct the style string
    return "; ".join(f"{key}:{value}" for key, value in style_dict.items())


def update_thickness_attribute(style):

    style_dict = dict(item.split(":")
                      for item in style.split(";") if ":" in item)

    # Halve stroke-width if it exists; otherwise, add it
    stroke_width = style_dict.get("stroke-width")
    if stroke_width is not None:
        try:
            if stroke_width.endswith("px"):
                value = float(stroke_width[:-2]) / 2
                style_dict["stroke-width"] = f"{value}px"
            else:
                value = float(stroke_width) / 2
                style_dict["stroke-width"] = str(value)
        except ValueError:
            print(stroke_width)
            pass  # Skip if non-numeric
    else:
        style_dict["stroke-width"] = "0.5"  # Add default reduced width

    return "; ".join(f"{key}:{value}" for key, value in style_dict.items())

def is_str_none(s):
    return (
        s is None or
        (isinstance(s, str) and ('none' in s.lower()))
    )

def replace_paths_with_shapes(svg_file, output_file):
    # Parse the SVG file
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(svg_file, parser)
    root = tree.getroot()

    # Define the SVG namespace
    namespace = {'svg': 'http://www.w3.org/2000/svg'}
    # fills = set()
    # Iterate through paths
    for path in root.xpath(".//svg:path", namespaces=namespace):
        # Get the 'd' attribute of the path
        path_data = path.attrib.get("d", "")
        style_string = style_dict = path.attrib.get('style', '')
        style_dict = dict(item.split(":")
                          for item in style_string.split(";") if ":" in item)

        # Classify the path
        shape_type = classify_path(path_data)
        props = generate_shape_properties(path, shape_type)
        for k, v in path.attrib.items():
            if k != "d":
                props[k] = v

        if shape_type in ['circle', 'rectangle', 'polygon']:
            props['style'] = update_fill_attribute(
                path.attrib.get('style', ''))
        props['style'] = update_thickness_attribute(
            path.attrib.get('style', ''))
        if 'clip-path' in props:
            clip_id = props['clip-path'].replace('url(#', '').replace(')', '')
            clip_def = root.xpath(
                f".//svg:*[@id='{clip_id}']", namespaces=namespace)
            if not clip_def:
                print(
                    f"Warning: Clipping path {clip_id} not found, removing clip-path")
                del props['clip-path']

        if shape_type == "rectangle":
            shape_type = "polygon"

        style_dict = dict(item.split(":")
                          for item in path.attrib.get('style', '').split(";") if ":" in item)
        original_fill = style_dict.get("fill", None)
        if shape_type == "polygon" and is_str_none(original_fill):
            pass
        else:
            new_element = etree.Element(shape_type, attrib=props)

            parent = path.getparent()  # Get the parent element
            parent.replace(path, new_element)

    tree.write(output_file, pretty_print=True,
               xml_declaration=True, encoding="utf-8")



def scale_polygon_with_line_rotation(polygon_points, xscale, yscale):
    """
    Scale a tilted rectangle polygon under non-uniform scaling, correcting for base-line angle change.

    Args:
        polygon_points: str of "x1,y1 x2,y2 ..."
        xscale, yscale: float scale factors

    Returns:
        str of new scaled points
    """
    points = [tuple(map(float, pair.split(",")))
              for pair in polygon_points.strip().split()]
    if len(points) < 2:
        raise ValueError("Need at least two points to infer rotation")

    # Compute center
    cx = sum(x for x, _ in points) / len(points)
    cy = sum(y for _, y in points) / len(points)
    cx_scaled = cx * xscale
    cy_scaled = cy * yscale

    # First edge defines original angle
    (x1, y1), (x2, y2) = points[0], points[1]
    dx, dy = x2 - x1, y2 - y1
    original_theta = math.atan2(dy, dx)

    # Line after scaling
    dx_scaled = dx * xscale
    dy_scaled = dy * yscale
    new_theta = math.atan2(dy_scaled, dx_scaled)

    rotation_correction = new_theta - original_theta

    cos_orig = math.cos(-original_theta)
    sin_orig = math.sin(-original_theta)
    cos_new = math.cos(original_theta + rotation_correction)
    sin_new = math.sin(original_theta + rotation_correction)

    new_points = []
    for x, y in points:
        # Translate to center
        x0, y0 = x - cx, y - cy

        # Undo original rotation
        xr = x0 * cos_orig - y0 * sin_orig
        yr = x0 * sin_orig + y0 * cos_orig

        # Scale
        xs = xr * xscale
        ys = yr * yscale

        # Apply corrected rotation
        x_rot = xs * cos_new - ys * sin_new
        y_rot = xs * sin_new + ys * cos_new

        # Translate to scaled center
        x_final = x_rot + cx_scaled
        y_final = y_rot + cy_scaled

        new_points.append(f"{x_final},{y_final}")

    return " ".join(new_points)


def make_square_and_scale_polygon(polygon_points, xscale, yscale, size_boost=1.0):
    """
    Convert a rectangle-like polygon to a square, scale it with aspect-aware rotation,
    and increase size slightly.

    Args:
        polygon_points: str — "x1,y1 x2,y2 ..." (should be 4 corners)
        xscale, yscale: float — scale factors
        size_boost: float — multiply side length by this (e.g., 1.1)

    Returns:
        str — scaled, square polygon points
    """
    points = [tuple(map(float, pair.split(",")))
              for pair in polygon_points.strip().split()]
    if len(points) != 4:
        # raise ValueError("Function expects exactly 4 points (rectangle)")
        # print(f"there are {len(points)} points rather than 4. returning the original points")
        # return " ".join(points)
        return polygon_points

    # Compute center
    cx = sum(x for x, _ in points) / 4
    cy = sum(y for _, y in points) / 4
    cx_scaled = cx * xscale
    cy_scaled = cy * yscale

    # Infer angle from first edge
    (x1, y1), (x2, y2) = points[0], points[1]
    dx, dy = x2 - x1, y2 - y1
    original_theta = math.atan2(dy, dx)

    # New rotated angle after skewed scaling
    dx_scaled = dx * xscale
    dy_scaled = dy * yscale
    new_theta = math.atan2(dy_scaled, dx_scaled)
    rotation_correction = new_theta - original_theta

    # De-rotation matrix (to compute axis-aligned sides)
    cos_orig = math.cos(-original_theta)
    sin_orig = math.sin(-original_theta)

    local_coords = []
    for x, y in points:
        x0, y0 = x - cx, y - cy
        xr = x0 * cos_orig - y0 * sin_orig
        yr = x0 * sin_orig + y0 * cos_orig
        local_coords.append((xr, yr))

    # Estimate width and height
    xs, ys = zip(*local_coords)
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    side = size_boost * max(width, height)

    # Build square centered at origin, then scale and rotate back
    half = side / 2
    square_local = [(-half, -half), (half, -half), (half, half), (-half, half)]

    # Rotate back to corrected orientation
    cos_new = math.cos(original_theta + rotation_correction)
    sin_new = math.sin(original_theta + rotation_correction)

    new_points = []
    for x, y in square_local:
        x_rot = x * cos_new - y * sin_new
        y_rot = x * sin_new + y * cos_new
        x_final = x_rot + cx_scaled
        y_final = y_rot + cy_scaled
        new_points.append(f"{x_final},{y_final}")

    return " ".join(new_points)


def scale_polygons(root, namespace, xscale_factor, yscale_factor):
    for poly in root.xpath(".//svg:polygon", namespaces=namespace):
        points = poly.attrib.get("points", "").strip()
        if not points:
            continue
        try:
            # new_points = scale_polygon_with_line_rotation(points, xscale_factor, yscale_factor)
            new_points = make_square_and_scale_polygon(
                points, xscale_factor, yscale_factor, size_boost=1.1)
            poly.attrib["points"] = new_points
        except Exception as e:
            print(f"Warning: Skipping malformed polygon: {e}")


def scale_rectangles(root, namespace, xscale_factor, yscale_factor):
    """Scale all rectangle elements."""
    for rect in root.xpath(".//svg:rect", namespaces=namespace):
        x = float(rect.attrib.get("x", "0")) * xscale_factor
        width = float(rect.attrib.get("width", "0")) * xscale_factor
        rect.attrib["x"] = str(x)
        rect.attrib["width"] = str(width)

        y = float(rect.attrib.get("y", "0")) * yscale_factor
        height = float(rect.attrib.get("height", "0")) * yscale_factor
        rect.attrib["y"] = str(y)
        rect.attrib["height"] = str(height)


def scale_lines(root, namespace, xscale_factor, yscale_factor):
    """Scale all line elements."""
    for line in root.xpath(".//svg:line", namespaces=namespace):
        x1 = float(line.attrib.get("x1", "0")) * xscale_factor
        x2 = float(line.attrib.get("x2", "0")) * xscale_factor
        line.attrib["x1"] = str(x1)
        line.attrib["x2"] = str(x2)

        y1 = float(line.attrib.get("y1", "0")) * yscale_factor
        y2 = float(line.attrib.get("y2", "0")) * yscale_factor
        line.attrib["y1"] = str(y1)
        line.attrib["y2"] = str(y2)


def scale_paths(root, namespace, xscale_factor, yscale_factor):
    """Scale all path elements."""
    for path in root.xpath(".//svg:path", namespaces=namespace):
        path_data = path.attrib.get("d", "")
        new_path_data = []
        tokens = path_data.replace(',', ' ').split()

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.upper() in ['M', 'L', 'H', 'V', 'C', 'S', 'Q', 'T', 'A', 'Z']:
                new_path_data.append(token)
                # Handle coordinates following commands
                if token.upper() in ['M', 'L']:  # MoveTo, LineTo
                    if i + 2 < len(tokens):
                        try:
                            x = float(tokens[i + 1]) * xscale_factor
                            y = float(tokens[i + 2]) * yscale_factor
                            new_path_data.extend([str(x), str(y)])
                            i += 2
                        except ValueError:
                            new_path_data.append(tokens[i + 1])
                elif token.upper() == 'H':  # Horizontal line
                    if i + 1 < len(tokens):
                        try:
                            x = float(tokens[i + 1]) * xscale_factor
                            new_path_data.append(str(x))
                            i += 1
                        except ValueError:
                            new_path_data.append(tokens[i + 1])
                elif token.upper() == 'V':  # Vertical line
                    if i + 1 < len(tokens):
                        try:
                            y = float(tokens[i + 1]) * yscale_factor
                            new_path_data.append(str(y))
                            i += 1
                        except ValueError:
                            new_path_data.append(tokens[i + 1])
            else:
                # Try to interpret as coordinate
                try:
                    number = float(token)
                    # This is a simplified approach - you might need more sophisticated
                    # path parsing for complex paths
                    new_path_data.append(str(number * xscale_factor))
                except ValueError:
                    new_path_data.append(token)
            i += 1

        path.attrib["d"] = " ".join(new_path_data)


def scale_circles(root, namespace, xscale_factor, yscale_factor):
    """Scale circle elements while preserving radius for specific circles."""
    # First pass: scale positions and find bounds
    cxmin, cxmax = float('inf'), float('-inf')
    for circle in root.xpath(".//svg:circle", namespaces=namespace):
        cx = float(circle.attrib.get("cx", "0")) * xscale_factor
        circle.attrib["cx"] = str(cx)
        cxmin, cxmax = min(cx, cxmin), max(cx, cxmax)

        cy = float(circle.attrib.get("cy", "0")) * yscale_factor
        circle.attrib["cy"] = str(cy)

    # Second pass: adjust radius based on position and fill
    for circle in root.xpath(".//svg:circle", namespaces=namespace):
        r = float(circle.attrib.get("r", "0"))
        cx = float(circle.attrib.get("cx", "0"))

        # Check if circle has fill in style attribute
        style = circle.attrib.get('style', '')
        has_fill = 'fill' in style

        if not has_fill and abs(cx - cxmin) > 0.01 and abs(cx - cxmax) > 0.01:
            circle.attrib["r"] = str(0)
        else:
            circle.attrib["r"] = str(r * 0.8)

def update_svg_canvas(root, xscale_factor, yscale_factor):
    """Update SVG canvas dimensions and viewBox."""
    # Update width attribute
    if 'width' in root.attrib:
        original_width = float(root.attrib['width'].replace('pt', ''))
        root.attrib['width'] = str(original_width * xscale_factor)

    # Update height attribute
    if 'height' in root.attrib:
        original_height = float(root.attrib['height'].replace('pt', ''))
        root.attrib['height'] = str(original_height * yscale_factor)

    # Update viewBox if it exists
    if 'viewBox' in root.attrib:
        viewbox_values = root.attrib['viewBox'].split()
        if len(viewbox_values) == 4:
            x, y, width, height = map(float, viewbox_values)
            new_viewbox = f"{x * xscale_factor} {y * yscale_factor} {width * xscale_factor} {height * yscale_factor}"
            root.attrib['viewBox'] = new_viewbox
            

def parse_svg_file(svg_file):
    """Parse SVG file and return tree and root with namespace."""
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(svg_file, parser)
    root = tree.getroot()
    namespace = {'svg': 'http://www.w3.org/2000/svg'}
    return tree, root, namespace


def save_svg_file(tree, output_file):
    """Save the modified SVG tree to output file."""
    tree.write(output_file, pretty_print=True,
               xml_declaration=True, encoding="utf-8")


def scale_svg(svg_file, output_file, xscale_factor=0.5, yscale_factor=1.0):
    """
    Scale the width of an SVG while preserving certain elements (like circles).

    Args:
        svg_file (str): Path to the input SVG file.
        output_file (str): Path to save the modified SVG file.
        xscale_factor (float): Factor by which to scale horizontal coordinates.
        yscale_factor (float): Factor by which to scale vertical coordinates.
    """
    # Parse the SVG file
    tree, root, namespace = parse_svg_file(svg_file)

    # Update canvas dimensions
    update_svg_canvas(root, xscale_factor, yscale_factor)
    # update_svg_canvas_to_fit_content(root)

    # Scale different element types
    scale_rectangles(root, namespace, xscale_factor, yscale_factor)
    scale_lines(root, namespace, xscale_factor, yscale_factor)
    scale_polygons(root, namespace, xscale_factor, yscale_factor)
    scale_paths(root, namespace, xscale_factor, yscale_factor)
    scale_circles(root, namespace, xscale_factor, yscale_factor)

    # Save the modified SVG
    save_svg_file(tree, output_file)
