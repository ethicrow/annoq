"""Coordinate transformation helpers for image and canvas mapping."""


def image_to_canvas_coords(x, y, zoom, pan_x, pan_y, crop_x, crop_y):
    """Convert image pixel coordinates to canvas coordinates."""
    if zoom == 1.0:
        return x * zoom + pan_x, y * zoom + pan_y
    return (x - crop_x) * zoom, (y - crop_y) * zoom


def canvas_to_image_coords(x, y, zoom, pan_x, pan_y, crop_x, crop_y):
    """Convert canvas coordinates to image pixel coordinates."""
    if zoom == 1.0:
        return (x - pan_x) / zoom, (y - pan_y) / zoom
    return x / zoom + crop_x, y / zoom + crop_y
