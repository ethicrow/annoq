import os
import shutil
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
from yaml_dataset_loader import YamlDatasetLoader
from yolo_dataset import YoloDataset
from image_viewer import ImageViewer
from cache import get_cached_index, update_cache
import argparse
import cv2
from PIL import Image, ImageTk
import yaml

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional dependency
    YOLO = None

class App:
    def __init__(self, root, yaml_path=None, model_path=None):
        self.root = root
        self.root.title("YOLO Dataset Viewer")

        # Model / inference state
        self.model = None
        self.model_path = None
        self.inference_window = None
        self.inference_label = None
        self.inference_photo = None

        # Ask for YAML file
        if not yaml_path:
            yaml_path = filedialog.askopenfilename(
                title="Select YOLO data.yaml",
                filetypes=[("YAML files", "*.yaml *.yml")]
            )

        if not yaml_path:
            messagebox.showerror("Error", "No data.yaml file selected.")
            root.quit()
            return

        try:
            self.yaml_loader = YamlDatasetLoader(yaml_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YAML:\n{str(e)}")
            root.quit()
            return

        self.yaml_path = os.path.abspath(yaml_path)
        cached_index = get_cached_index(self.yaml_path)

        splits = self.yaml_loader.get_dataset_splits()
        if not splits:
            messagebox.showerror("Error", "No valid dataset splits found in YAML.")
            root.quit()
            return

        # Create YoloDataset instances for each split
        self.datasets = {}
        class_names = self.yaml_loader.get_class_names()
        for split in splits:
            paths = self.yaml_loader.get_paths(split)
            ds = YoloDataset(paths["images"], paths["labels"], class_names)
            if cached_index is not None:
                ds.set_index(cached_index)
            self.datasets[split] = ds

        # GUI dropdown to select split
        self.split_selector = ttk.Combobox(root, values=list(self.datasets.keys()), state="readonly")
        self.split_selector.current(0)
        self.split_selector.pack(pady=5)
        self.split_selector.bind("<<ComboboxSelected>>", self.on_split_selected)

        # Frame for stats/export buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Show Stats", command=self.show_stats).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Export", command=self.export_dataset).pack(side=tk.LEFT, padx=5)

        # Inference button on top right
        self.inference_button = tk.Button(root, text="Inference", command=self.on_inference_button)
        self.inference_button.place(relx=1.0, x=-10, y=10, anchor="ne")

        # Frame for image viewer
        self.viewer_frame = tk.Frame(root)
        self.viewer_frame.pack(fill="both", expand=True)

        self.current_dataset = self.datasets[self.split_selector.get()]
        self.viewer = None

        # Load model from CLI if provided
        if model_path:
            self.load_model(model_path)

        self.load_viewer()

    def load_viewer(self):
        for widget in self.viewer_frame.winfo_children():
            widget.destroy()

        self.viewer = ImageViewer(self.viewer_frame, self.current_dataset, index_callback=self.on_index_update)
        self.viewer.pack(fill="both", expand=True)

    def on_split_selected(self, event=None):
        split = self.split_selector.get()
        self.current_dataset = self.datasets[split]
        self.load_viewer()

    def show_stats(self):
        stats = self.current_dataset.compute_stats()
        win = tk.Toplevel(self.root)
        win.title("Dataset Stats")
        text = tk.Text(win, width=50, height=20)
        text.pack(padx=10, pady=10)
        text.insert(tk.END, f"Total images: {stats['total_images']}\n")
        text.insert(tk.END, f"Background images: {stats['background_images']}\n\n")
        text.insert(tk.END, "Class occurrences:\n")
        for name, count in stats['class_counts'].items():
            text.insert(tk.END, f"  {name}: {count}\n")
        text.config(state=tk.DISABLED)

    def export_dataset(self):
        dataset_name = simpledialog.askstring("Export Dataset", "Enter name for the exported dataset:")
        if not dataset_name:
            return
        base_dir = filedialog.askdirectory(
            title="Select directory for export",
            initialdir=os.path.dirname(self.yaml_path),
        )
        if not base_dir:
            return
        export_dir = os.path.join(base_dir, dataset_name)
        images_dir = os.path.join(export_dir, "images")
        labels_dir = os.path.join(export_dir, "labels")
        if os.path.exists(export_dir):
            messagebox.showerror("Error", f"Directory '{export_dir}' already exists.")
            return
        try:
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(labels_dir, exist_ok=True)
            current_idx = self.current_dataset.current_index()
            for img_path in self.current_dataset.image_paths[: current_idx + 1]:
                shutil.copy2(img_path, images_dir)
                base = os.path.splitext(os.path.basename(img_path))[0]
                label_src = os.path.join(self.current_dataset.label_dir, base + ".txt")
                if os.path.exists(label_src):
                    shutil.copy2(label_src, labels_dir)
            data = {
                "names": self.yaml_loader.get_class_names(),
                "train": os.path.relpath(images_dir, export_dir),
            }
            with open(os.path.join(export_dir, "data.yaml"), "w") as f:
                yaml.safe_dump(data, f)
            messagebox.showinfo("Export Complete", f"Dataset exported to {export_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{e}")

    def on_index_update(self, index):
        update_cache(self.yaml_path, index)
        self.run_inference_on_current_image()

    def load_model(self, path):
        if YOLO is None:
            messagebox.showerror("Error", "Ultralytics YOLO is not installed.")
            return False
        try:
            self.model = YOLO(path)
            self.model_path = path
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model:\n{e}")
            return False

    def on_inference_button(self):
        if self.model is None:
            model_path = filedialog.askopenfilename(
                title="Select model file",
                filetypes=[("Model Files", "*.pt *.onnx *.pth"), ("All Files", "*.*")]
            )
            if not model_path:
                return
            if not self.load_model(model_path):
                return
        self.open_inference_window()

    def open_inference_window(self):
        if self.inference_window and self.inference_window.winfo_exists():
            return
        self.inference_window = tk.Toplevel(self.root)
        self.inference_window.title("Inference")
        self.inference_window.attributes("-topmost", True)
        self.inference_window.protocol("WM_DELETE_WINDOW", self.close_inference_window)
        self.inference_label = tk.Label(self.inference_window)
        self.inference_label.pack()
        self.run_inference_on_current_image()

    def close_inference_window(self):
        if self.inference_window:
            self.inference_window.destroy()
            self.inference_window = None
            self.inference_label = None
            self.inference_photo = None

    def run_inference_on_current_image(self):
        if not (self.model and self.inference_window and self.inference_window.winfo_exists()):
            return
        try:
            image_path = self.current_dataset.current_image_path()
            results = self.model(image_path)
            if not results:
                return
            img = results[0].plot()
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img)
            self.inference_photo = ImageTk.PhotoImage(pil_img)
            self.inference_label.config(image=self.inference_photo)
        except Exception as e:
            messagebox.showerror("Error", f"Inference failed:\n{e}")
            self.close_inference_window()

def parse_args():
    parser = argparse.ArgumentParser(description="AnnoQ - Simple Image Annotation Tool")
    parser.add_argument("--yaml", help="Path to YAML dataset config file")
    parser.add_argument("--model", help="Path to YOLO model file", default=None)
    return parser.parse_args()

if __name__ == "__main__":

    args = parse_args()
    root = tk.Tk()
    app = App(root, args.yaml if args.yaml else None, model_path=args.model)
    root.mainloop()
