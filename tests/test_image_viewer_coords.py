import pytest

from coords import image_to_canvas_coords, canvas_to_image_coords


def round_pair(pair):
    return pytest.approx(pair[0]), pytest.approx(pair[1])


def test_transform_identity_with_pan():
    x, y = 50, 30
    zoom = 1.0
    pan_x, pan_y = 100, 40
    crop_x = crop_y = 0
    cx, cy = image_to_canvas_coords(x, y, zoom, pan_x, pan_y, crop_x, crop_y)
    assert (cx, cy) == (150, 70)
    ix, iy = canvas_to_image_coords(cx, cy, zoom, pan_x, pan_y, crop_x, crop_y)
    assert round_pair((ix, iy)) == (x, y)


def test_transform_with_zoom_and_crop():
    x, y = 50, 80
    zoom = 2.0
    pan_x = pan_y = 0
    crop_x, crop_y = 40, 60
    cx, cy = image_to_canvas_coords(x, y, zoom, pan_x, pan_y, crop_x, crop_y)
    assert (cx, cy) == (20, 40)
    ix, iy = canvas_to_image_coords(cx, cy, zoom, pan_x, pan_y, crop_x, crop_y)
    assert round_pair((ix, iy)) == (x, y)
