import os
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageEnhance
import numpy as np


def resize_with_letterbox(image, size):
    """Resize image to size (w, h) with letterbox to preserve aspect ratio."""
    target_w, target_h = size
    h, w = image.shape[:2]
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(image, (new_w, new_h))
    canvas = np.zeros((target_h, target_w, 3), dtype=image.dtype)
    top = (target_h - new_h) // 2
    left = (target_w - new_w) // 2
    canvas[top:top + new_h, left:left + new_w] = resized
    return canvas


class AugmentationWindow:
    def __init__(self, parent, images_dir, labels_dir, frame_size):
        self.parent = parent
        self.images_dir = images_dir
        self.labels_dir = labels_dir
        self.frame_size = frame_size
        self.top = tk.Toplevel(parent)
        self.top.title("Augment Images")
        self.flip_h = tk.BooleanVar()
        self.flip_v = tk.BooleanVar()
        self.rotate = tk.BooleanVar()
        self.bright = tk.BooleanVar()
        tk.Checkbutton(self.top, text="Horizontal Flip", variable=self.flip_h).pack(anchor="w")
        tk.Checkbutton(self.top, text="Vertical Flip", variable=self.flip_v).pack(anchor="w")
        tk.Checkbutton(self.top, text="Rotate 90°", variable=self.rotate).pack(anchor="w")
        tk.Checkbutton(self.top, text="Increase Brightness", variable=self.bright).pack(anchor="w")
        tk.Button(self.top, text="Apply", command=self.apply).pack(pady=10)

    def apply(self):
        images = [f for f in os.listdir(self.images_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        for img_name in images:
            path = os.path.join(self.images_dir, img_name)
            img = Image.open(path)
            base = os.path.splitext(img_name)[0]
            if self.flip_h.get():
                self.save_augmented(img.transpose(Image.FLIP_LEFT_RIGHT), base + "_hflip")
            if self.flip_v.get():
                self.save_augmented(img.transpose(Image.FLIP_TOP_BOTTOM), base + "_vflip")
            if self.rotate.get():
                self.save_augmented(img.rotate(90, expand=True), base + "_rot90")
            if self.bright.get():
                enhancer = ImageEnhance.Brightness(img)
                self.save_augmented(enhancer.enhance(1.5), base + "_bright")
        messagebox.showinfo("Augmentation", "Augmentation completed")
        self.top.destroy()

    def save_augmented(self, pil_img, base_name):
        img_np = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        img_np = resize_with_letterbox(img_np, self.frame_size)
        out_path = os.path.join(self.images_dir, base_name + ".jpg")
        cv2.imwrite(out_path, img_np)
        open(os.path.join(self.labels_dir, base_name + ".txt"), "w").close()


class DatasetGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dataset Generator")
        self.dataset_dir = None
        self.images_dir = None
        self.labels_dir = None
        self.frame_size = (640, 640)
        self.frame_counter = 0
        self.build_wizard()

    def build_wizard(self):
        self.wizard = tk.Frame(self.root)
        self.wizard.pack(padx=10, pady=10)
        tk.Label(self.wizard, text="Dataset Name:").grid(row=0, column=0, sticky="e")
        self.name_entry = tk.Entry(self.wizard, width=30)
        self.name_entry.grid(row=0, column=1, padx=5)
        tk.Label(self.wizard, text="Output Directory:").grid(row=1, column=0, sticky="e")
        self.dir_entry = tk.Entry(self.wizard, width=30)
        self.dir_entry.grid(row=1, column=1, padx=5)
        tk.Button(self.wizard, text="Browse", command=self.browse_dir).grid(row=1, column=2)
        tk.Label(self.wizard, text="Frame Size (WxH):").grid(row=2, column=0, sticky="e")
        self.size_entry = tk.Entry(self.wizard, width=30)
        self.size_entry.insert(0, "1280x1280")
        self.size_entry.grid(row=2, column=1, padx=5)
        tk.Button(self.wizard, text="Next", command=self.finish_wizard).grid(row=3, column=0, columnspan=3, pady=10)

    def browse_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def finish_wizard(self):
        name = self.name_entry.get().strip()
        directory = self.dir_entry.get().strip()
        size_str = self.size_entry.get().lower().replace("x", " ")
        try:
            w, h = map(int, size_str.split())
        except Exception:
            messagebox.showerror("Error", "Invalid frame size")
            return
        if not name or not directory:
            messagebox.showerror("Error", "Please fill all fields")
            return
        self.dataset_dir = os.path.join(directory, name)
        if os.path.exists(self.dataset_dir):
            messagebox.showerror("Error", f"Directory '{self.dataset_dir}' already exists")
            return
        self.images_dir = os.path.join(self.dataset_dir, "images")
        self.labels_dir = os.path.join(self.dataset_dir, "labels")
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.labels_dir, exist_ok=True)
        self.frame_size = (w, h)
        self.wizard.destroy()
        self.build_main_ui()

    def build_main_ui(self):
        self.main = tk.Frame(self.root)
        self.main.pack(padx=10, pady=10)
        tk.Label(self.main, text=f"Dataset: {self.dataset_dir}").pack(pady=5)
        tk.Button(self.main, text="Add Videos", command=self.add_videos).pack(fill="x", pady=2)
        tk.Button(self.main, text="Add Images", command=self.add_images).pack(fill="x", pady=2)
        tk.Button(self.main, text="Augment Images", command=self.open_augment).pack(fill="x", pady=2)

    def add_videos(self):
        paths = filedialog.askopenfilenames(title="Select Videos", filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")])
        for path in paths:
            self.process_video(path)
        if paths:
            messagebox.showinfo("Done", "Finished extracting frames")

    def add_images(self):
        paths = filedialog.askopenfilenames(title="Select Images", filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp"), ("All Files", "*.*")])
        for path in paths:
            self.process_image(path)
        if paths:
            messagebox.showinfo("Done", "Finished copying images")

    def process_video(self, path):
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            messagebox.showerror("Error", f"Failed to open video: {path}")
            return
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = resize_with_letterbox(frame, self.frame_size)
            self.save_frame(frame)
        cap.release()

    def process_image(self, path):
        img = cv2.imread(path)
        if img is None:
            messagebox.showerror("Error", f"Failed to read image: {path}")
            return
        img = resize_with_letterbox(img, self.frame_size)
        self.save_frame(img)

    def save_frame(self, frame):
        name = f"frame_{self.frame_counter:06d}"
        img_path = os.path.join(self.images_dir, name + ".jpg")
        cv2.imwrite(img_path, frame)
        open(os.path.join(self.labels_dir, name + ".txt"), "w").close()
        self.frame_counter += 1

    def open_augment(self):
        if not os.listdir(self.images_dir):
            messagebox.showerror("Error", "No images to augment")
            return
        AugmentationWindow(self.root, self.images_dir, self.labels_dir, self.frame_size)


def main():
    root = tk.Tk()
    DatasetGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
