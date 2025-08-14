import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bounding_box import BoundingBox


def test_to_pixel_rect():
    box = BoundingBox(class_id=0, x_center=0.5, y_center=0.5, width=0.2, height=0.4)
    img_w, img_h = 100, 200
    assert box.to_pixel_rect(img_w, img_h) == (40, 60, 60, 140)


def test_contains_point_inside():
    box = BoundingBox(class_id=0, x_center=0.5, y_center=0.5, width=0.2, height=0.4)
    img_w, img_h = 100, 200
    assert box.contains_point(50, 100, img_w, img_h)


def test_contains_point_outside():
    box = BoundingBox(class_id=0, x_center=0.5, y_center=0.5, width=0.2, height=0.4)
    img_w, img_h = 100, 200
    assert not box.contains_point(10, 10, img_w, img_h)


def test_from_pixel_coords_rejects_small_box():
    img_w = img_h = 100
    box = BoundingBox.from_pixel_coords(0, 0, 0, 5, 5, img_w, img_h)
    assert box is None


def test_from_pixel_coords_creates_box():
    img_w = img_h = 100
    box = BoundingBox.from_pixel_coords(0, 10, 10, 30, 30, img_w, img_h, "test")
    assert box is not None
    assert box.to_pixel_rect(img_w, img_h) == (10, 10, 30, 30)
