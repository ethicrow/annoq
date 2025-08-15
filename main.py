import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from yaml_dataset_loader import YamlDatasetLoader
from yolo_dataset import YoloDataset
from image_viewer import ImageViewer
from cache import get_cached_index, update_cache
import argparse

class App:
    def __init__(self, root, yaml_path=None):
        self.root = root
        self.root.title("YOLO Dataset Viewer")

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

        # Button to show dataset statistics
        tk.Button(root, text="Show Stats", command=self.show_stats).pack(pady=5)

        # Frame for image viewer
        self.viewer_frame = tk.Frame(root)
        self.viewer_frame.pack(fill="both", expand=True)

        self.current_dataset = self.datasets[self.split_selector.get()]
        self.viewer = None
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

    def on_index_update(self, index):
        update_cache(self.yaml_path, index)

def parse_args():
    parser = argparse.ArgumentParser(description="AnnoQ - Simple Image Annotation Tool")
    parser.add_argument("--yaml", help="Path to YAML dataset config file")
    return parser.parse_args()

if __name__ == "__main__":

    args = parse_args()
    root = tk.Tk()
    app = App(root, args.yaml if args.yaml else None)
    root.mainloop()
