import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bounding_box import BoundingBox, smallest_box_containing_point


def test_selects_smallest_overlapping_box():
    img_w = img_h = 100
    big = BoundingBox.from_pixel_coords(0, 10, 10, 90, 90, img_w, img_h)
    small = BoundingBox.from_pixel_coords(0, 40, 40, 60, 60, img_w, img_h)
    # Click inside both boxes
    selected = smallest_box_containing_point([big, small], 50, 50, img_w, img_h)
    assert selected == small


def test_returns_none_when_no_box_contains_point():
    img_w = img_h = 100
    box = BoundingBox.from_pixel_coords(0, 10, 10, 30, 30, img_w, img_h)
    selected = smallest_box_containing_point([box], 50, 50, img_w, img_h)
    assert selected is None
