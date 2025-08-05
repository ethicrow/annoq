# bounding_box.py

import random

class BoundingBox:
    def __init__(self, class_id, x_center, y_center, width, height, class_name=""):
        self.class_id = class_id
        self.class_name = class_name
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        self.color = self._generate_color(class_id)

    def _generate_color(self, seed):
        random.seed(seed)
        return "#{:06x}".format(random.randint(0x111111, 0xFFFFFF))

    def to_yolo_format(self):
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"

    def to_pixel_rect(self, img_w, img_h):
        x1 = int((self.x_center - self.width / 2) * img_w)
        y1 = int((self.y_center - self.height / 2) * img_h)
        x2 = int((self.x_center + self.width / 2) * img_w)
        y2 = int((self.y_center + self.height / 2) * img_h)
        return x1, y1, x2, y2

    def contains_point(self, x, y, img_w, img_h):
        x1, y1, x2, y2 = self.to_pixel_rect(img_w, img_h)
        return x1 <= x <= x2 and y1 <= y <= y2
