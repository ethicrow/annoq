import platform
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import os
from bounding_box import BoundingBox, smallest_box_containing_point
from coords import image_to_canvas_coords, canvas_to_image_coords


class ImageViewer(tk.Frame):
    def __init__(self, root, dataset):
        super().__init__(root)
        self.dataset = dataset

        self.boxes = []
        self.selected_box = None
        self.dragging = False
        self.start_draw = None
        self.show_boxes = tk.BooleanVar(value=True)

        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.crop_x = 0
        self.crop_y = 0

        self.panning = False
        self.pan_start = None

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        info_frame = tk.Frame(self.main_frame)
        info_frame.pack(side="left", fill="y")

        self.info_scroll = tk.Scrollbar(info_frame)
        self.info_scroll.pack(side="right", fill="y")

        self.info_text = tk.Text(
            info_frame, width=40, yscrollcommand=self.info_scroll.set
        )
        self.info_text.pack(side="left", fill="both", expand=True)
        self.info_text.config(state=tk.DISABLED)
        self.info_scroll.config(command=self.info_text.yview)

        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.focus_set()

        ctrl_frame = tk.Frame(self)
        ctrl_frame.pack()

        tk.Button(ctrl_frame, text="← Prev", command=self.prev_image).pack(side="left")
        tk.Button(ctrl_frame, text="Next →", command=self.next_image).pack(side="left")
        tk.Button(ctrl_frame, text="Save", command=self.save_labels).pack(side="left")
        tk.Button(ctrl_frame, text="Clear Labels", command=self.clear_label_file).pack(side="left")
        tk.Label(ctrl_frame, text="Image").pack(side="left")
        self.index_var = tk.StringVar(value="1")
        idx_entry = tk.Entry(ctrl_frame, width=5, textvariable=self.index_var)
        idx_entry.pack(side="left")
        self.total_label = tk.Label(ctrl_frame, text=f"/{self.dataset.total_images()}")
        self.total_label.pack(side="left")
        idx_entry.bind_all("<Return>", self.on_index_change)
        self.canvas.bind_all("<Left>", lambda e: self.prev_image())
        self.canvas.bind_all("<Right>", lambda e: self.next_image())
        tk.Checkbutton(ctrl_frame, text="Show Boxes", variable=self.show_boxes, command=self.refresh).pack(side="left")

        self.canvas.bind_all("<Button-1>", lambda event: event.widget.focus_set())
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Delete>", self.delete_selected)
        if platform.system() == "Linux":
            self.canvas.bind('<Button-4>', self.mouseWheelHandler)
            self.canvas.bind('<Button-5>', self.mouseWheelHandler)
        else:
            self.canvas.bind('<MouseWheel>', self.mouseWheelHandler)

        self.canvas.bind("<Button-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self.on_pan_end)

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
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.crop_x = 0
        self.crop_y = 0
        self.index_var.set(str(self.dataset.current_index() + 1))
        self.total_label.config(text=f"/{self.dataset.total_images()}")
        self.refresh()
        self.update_info_area()

    def update_info_area(self):
        image_name = os.path.basename(self.dataset.current_image_path())
        label_path = self.dataset.current_label_path()
        label_name = os.path.basename(label_path)
        if os.path.exists(label_path):
            with open(label_path) as f:
                content = f.read()
        else:
            content = ""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, f"Image: {image_name}\n")
        self.info_text.insert(tk.END, f"Labels: {label_name}\n\n")
        self.info_text.insert(tk.END, content)
        self.info_text.config(state=tk.DISABLED)

    def refresh(self):
        self.canvas.delete("box")
        # Redraw image at new zoom/pan (draw image first)
        self.redraw_image()
        if not self.show_boxes.get():
            return
        for box in self.boxes:
            x1, y1, x2, y2 = box.to_pixel_rect(self.img_pil.width, self.img_pil.height)
            # Apply zoom, pan and crop
            x1, y1 = image_to_canvas_coords(
                x1, y1, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
            )
            x2, y2 = image_to_canvas_coords(
                x2, y2, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
            )
            color = box.color
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=4, tag="box")
            self.canvas.create_text(x1 + 5, y1 + 10, text=box.class_name, fill=color, anchor="nw", tag="box")

        # Draw current image index / total images at top right
        idx = self.dataset.current_index() + 1
        total = self.dataset.total_images()
        text = f"{idx}/{total}"
        if self.zoom == 1.0:
            tx = self.img_pil.width * self.zoom + self.pan_x - 10
            ty = 10 + self.pan_y
        else:
            tx = self.canvas.winfo_width() - 10
            ty = 10
        self.canvas.create_text(
            tx,
            ty,
            text=text,
            fill="white",
            anchor="ne",
            font=("Arial", 16, "bold"),
            tag="box"
        )

    def redraw_image(self):
        # Remove previous image
        self.canvas.delete("img")
        # Limit rendering to 16384x16384 pixels (increased from 4096)
        max_dim = 16384
        w = min(int(self.img_pil.width * self.zoom), max_dim)
        h = min(int(self.img_pil.height * self.zoom), max_dim)
        w = max(1, w)
        h = max(1, h)

        if self.zoom == 1.0:
            # Show the original image, centered if needed
            img_to_show = self.img_pil
            display_w, display_h = self.img_pil.width, self.img_pil.height
            pan_x, pan_y = self.pan_x, self.pan_y
            self.crop_x, self.crop_y = 0, 0
        else:
            # Calculate crop box in original image coordinates
            # The region of the image to show is (canvas_w, canvas_h) in display, but at 1/zoom scale in the image
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            # Center of the view in image coordinates
            center_x = (-self.pan_x + canvas_w / 2) / self.zoom
            center_y = (-self.pan_y + canvas_h / 2) / self.zoom
            # Size of the crop box in image coordinates
            crop_w = canvas_w / self.zoom
            crop_h = canvas_h / self.zoom
            # Crop box
            left = max(0, int(center_x - crop_w / 2))
            upper = max(0, int(center_y - crop_h / 2))
            right = min(self.img_pil.width, int(center_x + crop_w / 2))
            lower = min(self.img_pil.height, int(center_y + crop_h / 2))
            img_cropped = self.img_pil.crop((left, upper, right, lower))
            # Resize cropped region to fit canvas
            img_to_show = img_cropped.resize((canvas_w, canvas_h), Image.LANCZOS)
            display_w, display_h = canvas_w, canvas_h
            pan_x, pan_y = 0, 0
            self.crop_x, self.crop_y = left, upper

        self.image_tk = ImageTk.PhotoImage(img_to_show)
        self.canvas.create_image(pan_x, pan_y, anchor="nw", image=self.image_tk, tag="img")

    def on_click(self, event):
        # Adjust event coordinates for zoom and pan
        zx, zy = canvas_to_image_coords(
            event.x, event.y, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
        )
        box = smallest_box_containing_point(
            self.boxes, zx, zy, self.img_pil.width, self.img_pil.height
        )
        if box is not None:
            self.selected_box = box
            self.dragging = True
            return
        self.selected_box = None
        self.start_draw = (zx, zy)

    def on_drag(self, event):
        zx, zy = canvas_to_image_coords(
            event.x, event.y, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
        )
        if self.dragging and self.selected_box:
            w, h = self.img_pil.width, self.img_pil.height
            self.selected_box.x_center = zx / w
            self.selected_box.y_center = zy / h
            self.refresh()
        elif self.start_draw:
            self.refresh()
            x0, y0 = self.start_draw
            # Transform back to canvas coordinates for drawing
            x0c, y0c = image_to_canvas_coords(
                x0, y0, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
            )
            x1c, y1c = image_to_canvas_coords(
                zx, zy, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
            )
            self.canvas.create_rectangle(
                x0c, y0c, x1c, y1c, outline="white", dash=(4, 2), tag="box"
            )


    def on_release(self, event):
        if self.dragging:
            self.dragging = False
        elif self.start_draw:
            x0, y0 = self.start_draw
            x1, y1 = canvas_to_image_coords(
                event.x, event.y, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
            )
            w, h = self.img_pil.width, self.img_pil.height
            box = BoundingBox.from_pixel_coords(
                0, x0, y0, x1, y1, w, h, self.dataset.class_names[0]
            )
            if box:
                self.boxes.append(box)
            self.start_draw = None
            self.refresh()

    def on_right_click(self, event):
        zx, zy = canvas_to_image_coords(
            event.x, event.y, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
        )
        box = smallest_box_containing_point(
            self.boxes, zx, zy, self.img_pil.width, self.img_pil.height
        )
        if box is not None:
            self.selected_box = box
            menu = tk.Menu(self, tearoff=0)
            for i, name in enumerate(self.dataset.class_names):
                menu.add_command(label=name, command=lambda cid=i: self.change_box_class(cid))
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def mouseWheelHandler(self, event):
        if platform.system() == "Linux":
            delta = 1 if event.num == 4 else -1
        else:
            delta = event.delta
        if self.dragging and self.selected_box:
            scale_factor = 1.1 if delta > 0 else 0.9
            w, h = self.img_pil.width, self.img_pil.height
            new_w = self.selected_box.width * scale_factor
            new_h = self.selected_box.height * scale_factor
            min_w = 10 / w
            min_h = 10 / h
            self.selected_box.width = max(new_w, min_w)
            self.selected_box.height = max(new_h, min_h)
            self.refresh()
        else:
            # Zoom image at mouse pointer
            if platform.system() == "Linux":
                zoom_factor = 1.1 if delta > 0 else 0.9
            else:
                zoom_factor = 1.0 + (0.1 if delta > 0 else -0.1)
            # Compute min and max zoom so that image does not go below original size or exceed 4096x4096
            min_zoom = 1.0
            max_dim = 16384  # Increased from 4096
            max_zoom_w = max_dim / self.img_pil.width
            max_zoom_h = max_dim / self.img_pil.height
            max_zoom = min(max_zoom_w, max_zoom_h)
            new_zoom = max(min_zoom, min(max_zoom, self.zoom * zoom_factor))
            if new_zoom == self.zoom:
                return
            mouse_x, mouse_y = event.x, event.y
            rel_x, rel_y = canvas_to_image_coords(
                mouse_x, mouse_y, self.zoom, self.pan_x, self.pan_y, self.crop_x, self.crop_y
            )
            self.zoom = new_zoom
            if self.zoom == 1.0:
                # Center image on canvas
                canvas_w = self.canvas.winfo_width()
                canvas_h = self.canvas.winfo_height()
                self.pan_x = (canvas_w - self.img_pil.width) // 2
                self.pan_y = (canvas_h - self.img_pil.height) // 2
            else:
                self.pan_x = mouse_x - rel_x * self.zoom
                self.pan_y = mouse_y - rel_y * self.zoom
            self.refresh()

    def on_pan_start(self, event):
        if self.zoom > 1.0:
            self.panning = True
            self.pan_start = (event.x, event.y, self.pan_x, self.pan_y)

    def on_pan_move(self, event):
        if self.panning and self.zoom > 1.0 and self.pan_start:
            x0, y0, pan_x0, pan_y0 = self.pan_start
            dx = event.x - x0
            dy = event.y - y0
            new_pan_x = pan_x0 + dx
            new_pan_y = pan_y0 + dy

            # Calculate canvas and crop region
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            crop_w = canvas_w / self.zoom
            crop_h = canvas_h / self.zoom

            # Compute allowed pan range so crop stays within image
            min_pan_x = int(canvas_w - self.img_pil.width * self.zoom)
            max_pan_x = 0
            min_pan_y = int(canvas_h - self.img_pil.height * self.zoom)
            max_pan_y = 0

            # Clamp pan so that the image does not move out of bounds
            self.pan_x = min(max(new_pan_x, min_pan_x), max_pan_x)
            self.pan_y = min(max(new_pan_y, min_pan_y), max_pan_y)
            self.refresh()

    def on_pan_end(self, event):
        self.panning = False
        self.pan_start = None

    def on_index_change(self, event=None):
        try:
            new_idx = int(self.index_var.get()) - 1
        except ValueError:
            return
        self.dataset.set_index(new_idx)
        self.load_image()

    def delete_selected(self, event=None):
        if self.selected_box:
            self.boxes.remove(self.selected_box)
            self.selected_box = None
            self.refresh()

    def change_box_class(self, class_id):
        if self.selected_box is not None:
            self.selected_box.class_id = class_id
            if class_id < len(self.dataset.class_names):
                self.selected_box.class_name = self.dataset.class_names[class_id]
            else:
                self.selected_box.class_name = str(class_id)
            self.selected_box.color = self.selected_box._generate_color(class_id)
            self.refresh()

    def save_labels(self):
        self.dataset.save_labels(self.boxes)
        self.update_info_area()

    def clear_label_file(self):
        self.boxes = []
        self.selected_box = None
        self.dataset.save_labels(self.boxes)
        self.refresh()
        self.update_info_area()

    def next_image(self):
        self.dataset.next()
        self.load_image()

    def prev_image(self):
        self.dataset.prev()
        self.load_image()
