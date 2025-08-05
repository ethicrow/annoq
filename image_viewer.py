import platform
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
from bounding_box import BoundingBox


class ImageViewer(tk.Frame):
    def __init__(self, root, dataset):
        super().__init__(root)
        self.dataset = dataset

        self.boxes = []
        self.selected_box = None
        self.dragging = False
        self.start_draw = None
        self.show_boxes = tk.BooleanVar(value=True)

        self.canvas = tk.Canvas(self)
        self.canvas.pack()

        ctrl_frame = tk.Frame(self)
        ctrl_frame.pack()

        tk.Button(ctrl_frame, text="← Prev", command=self.prev_image).pack(side="left")
        tk.Button(ctrl_frame, text="Next →", command=self.next_image).pack(side="left")
        tk.Button(ctrl_frame, text="Save", command=self.save_labels).pack(side="left")
        tk.Checkbutton(ctrl_frame, text="Show Boxes", variable=self.show_boxes, command=self.refresh).pack(side="left")

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Delete>", self.delete_selected)
        if platform.system() == "Linux":
            self.canvas.bind('<Button-4>', self.mouseWheelHandler)
            self.canvas.bind('<Button-5>', self.mouseWheelHandler)
        else:
            self.canvas.bind('<MouseWheel>', self.mouseWheelHandler)

        self.load_image()

    def load_image(self):
        path = self.dataset.current_image_path()
        self.img_cv = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
        self.img_pil = Image.fromarray(self.img_cv)
        self.image_tk = ImageTk.PhotoImage(self.img_pil)
        self.canvas.config(width=self.img_pil.width, height=self.img_pil.height)
        self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)
        self.boxes = self.dataset.load_labels()
        self.selected_box = None
        self.refresh()

    def refresh(self):
        self.canvas.delete("box")
        if not self.show_boxes.get():
            return
        for box in self.boxes:
            x1, y1, x2, y2 = box.to_pixel_rect(self.img_pil.width, self.img_pil.height)
            color = box.color
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=4, tag="box")
            self.canvas.create_text(x1 + 5, y1 + 10, text=box.class_name, fill=color, anchor="nw", tag="box")

    def on_click(self, event):
        for box in reversed(self.boxes):
            if box.contains_point(event.x, event.y, self.img_pil.width, self.img_pil.height):
                self.selected_box = box
                self.dragging = True
                return
        self.selected_box = None
        self.start_draw = (event.x, event.y)

    def on_drag(self, event):
        if self.dragging and self.selected_box:
            w, h = self.img_pil.width, self.img_pil.height
            self.selected_box.x_center = event.x / w
            self.selected_box.y_center = event.y / h
            self.refresh()
        elif self.start_draw:
            self.refresh()
            x0, y0 = self.start_draw
            self.canvas.create_rectangle(x0, y0, event.x, event.y, outline="white", dash=(4, 2), tag="box")

    def on_release(self, event):
        if self.dragging:
            self.dragging = False
        elif self.start_draw:
            x0, y0 = self.start_draw
            x1, y1 = event.x, event.y
            w, h = self.img_pil.width, self.img_pil.height
            xc = ((x0 + x1) / 2) / w
            yc = ((y0 + y1) / 2) / h
            bw = abs(x1 - x0) / w
            bh = abs(y1 - y0) / h
            self.boxes.append(BoundingBox(0, xc, yc, bw, bh, self.dataset.class_names[0]))
            self.start_draw = None
            self.refresh()

    def mouseWheelHandler(self, event):
        if platform.system() == "Linux":
            delta = 1 if event.num == 4 else -1
        else:
            delta = event.delta
        if self.dragging and self.selected_box:
            scale_factor = 1.1 if delta > 0 else 0.9
            self.selected_box.width *= scale_factor
            self.selected_box.height *= scale_factor
            self.refresh()

    def delete_selected(self, event=None):
        if self.selected_box:
            self.boxes.remove(self.selected_box)
            self.selected_box = None
            self.refresh()

    def save_labels(self):
        self.dataset.save_labels(self.boxes)

    def next_image(self):
        self.dataset.next()
        self.load_image()

    def prev_image(self):
        self.dataset.prev()
        self.load_image()
