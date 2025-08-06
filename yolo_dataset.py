# yolo_dataset.py

import os
import glob
from bounding_box import BoundingBox

class YoloDataset:
    def __init__(self, image_dir, label_dir, class_names):
        self.image_dir = image_dir
        self.label_dir = label_dir
        self.image_paths = sorted(glob.glob(os.path.join(image_dir, "*")))
        self.index = 0
        self.class_names = class_names

    def current_image_path(self):
        return self.image_paths[self.index]

    def current_label_path(self):
        base = os.path.splitext(os.path.basename(self.current_image_path()))[0]
        return os.path.join(self.label_dir, base + ".txt")

    def load_labels(self):
        boxes = []
        path = self.current_label_path()
        if not os.path.exists(path):
            return boxes
        with open(path) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                class_id = int(parts[0])
                xc, yc, w, h = map(float, parts[1:])
                name = self.class_names[class_id] if class_id < len(self.class_names) else str(class_id)
                boxes.append(BoundingBox(class_id, xc, yc, w, h, name))
        return boxes

    def save_labels(self, boxes):
        with open(self.current_label_path(), "w") as f:
            for box in boxes:
                f.write(box.to_yolo_format() + "\n")

    def next(self):
        if self.index < len(self.image_paths) - 1:
            self.index += 1

    def prev(self):
        if self.index > 0:
            self.index -= 1
    
    def current_index(self):
        return self.index

    def total_images(self):
        return len(self.image_paths)
