import os
import json
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
from PIL import Image, ImageTk

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional dependency
    YOLO = None

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".annoq_video_cache.json")


class VideoInferenceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Inference Player")

        # State variables
        self.model = None
        self.cap = None
        self.running = False
        self.last_frame_time = time.time()
        self.roi_center = None
        self.roi_size = 100

        # Tk variables
        self.model_path = tk.StringVar()
        self.video_path = tk.StringVar()
        self.max_fps = tk.DoubleVar(value=30.0)
        self.force_size = tk.BooleanVar(value=False)
        self.resize_w = tk.IntVar(value=640)
        self.resize_h = tk.IntVar(value=480)
        self.enable_roi = tk.BooleanVar(value=False)

        self.info_roi_size = tk.StringVar(value="ROI: disabled")
        self.info_inference = tk.StringVar(value="Inference: N/A")
        self.info_fps = tk.StringVar(value="True FPS: 0.00")

        self._load_cache()

        # Layout
        self.video_label = tk.Label(root)
        self.video_label.pack(side=tk.LEFT, padx=5, pady=5)

        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        tk.Button(control_frame, text="Select Model", command=self.select_model).pack(fill=tk.X)
        tk.Button(control_frame, text="Select Video", command=self.select_video).pack(fill=tk.X, pady=5)

        tk.Label(control_frame, text="Max FPS").pack(anchor="w")
        tk.Entry(control_frame, textvariable=self.max_fps, width=7).pack(anchor="w")

        size_frame = tk.LabelFrame(control_frame, text="Force Size")
        size_frame.pack(fill=tk.X, pady=5)
        tk.Checkbutton(size_frame, text="Enable", variable=self.force_size).pack(anchor="w")
        tk.Entry(size_frame, textvariable=self.resize_w, width=5).pack(side=tk.LEFT)
        tk.Entry(size_frame, textvariable=self.resize_h, width=5).pack(side=tk.LEFT)

        tk.Checkbutton(control_frame, text="Enable ROI", variable=self.enable_roi).pack(pady=5, anchor="w")

        self.start_button = tk.Button(control_frame, text="Start", command=self.toggle_start)
        self.start_button.pack(fill=tk.X, pady=5)

        info_frame = tk.LabelFrame(control_frame, text="Info")
        info_frame.pack(fill=tk.X, pady=5)
        tk.Label(info_frame, textvariable=self.info_roi_size).pack(anchor="w")
        tk.Label(info_frame, textvariable=self.info_inference).pack(anchor="w")
        tk.Label(info_frame, textvariable=self.info_fps).pack(anchor="w")

        self.video_label.bind("<Motion>", self.on_mouse_move)
        self.video_label.bind("<MouseWheel>", self.on_mouse_wheel)
        self.video_label.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.video_label.bind("<Button-5>", self.on_mouse_wheel)  # Linux

        if self.model_path.get() and os.path.exists(self.model_path.get()):
            self._load_model(self.model_path.get())
        if self.video_path.get() and os.path.exists(self.video_path.get()):
            self.cap = cv2.VideoCapture(self.video_path.get())

    def select_model(self):
        path = filedialog.askopenfilename(
            title="Select model",
            filetypes=[("Model Files", "*.pt *.onnx *.pth"), ("All Files", "*.*")],
        )
        if path and self._load_model(path):
            self.model_path.set(path)
            self._save_cache()

    def _load_model(self, path):
        if YOLO is None:
            messagebox.showerror("Error", "Ultralytics YOLO is not installed.")
            return False
        try:
            self.model = YOLO(path)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model:\n{e}")
            return False

    def select_video(self):
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov"), ("All Files", "*.*")],
        )
        if path:
            self.video_path.set(path)
            self._save_cache()
            if self.cap:
                self.cap.release()
            self.cap = cv2.VideoCapture(path)

    def toggle_start(self):
        if not self.running:
            if not self.model:
                messagebox.showwarning("Warning", "Select a model first.")
                return
            if not self.cap:
                messagebox.showwarning("Warning", "Select a video first.")
                return
            self.running = True
            self.start_button.config(text="Stop")
            self.last_frame_time = time.time()
            self._process_frame()
        else:
            self.running = False
            self.start_button.config(text="Start")

    def _process_frame(self):
        if not self.running:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.toggle_start()
            return

        if self.force_size.get():
            frame = cv2.resize(frame, (self.resize_w.get(), self.resize_h.get()))

        roi_text = "ROI: disabled"
        start_time = time.time()
        if self.enable_roi.get() and self.roi_center:
            size = self.roi_size
            x, y = self.roi_center
            x1 = max(x - size // 2, 0)
            y1 = max(y - size // 2, 0)
            x2 = min(x1 + size, frame.shape[1])
            y2 = min(y1 + size, frame.shape[0])
            roi = frame[y1:y2, x1:x2]
            results = self.model(roi)
            if results:
                plotted = results[0].plot()
                frame[y1:y2, x1:x2] = plotted
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            roi_text = f"ROI size: {size}"
        else:
            results = self.model(frame)
            if results:
                frame = results[0].plot()
        inf_time = time.time() - start_time
        self.info_inference.set(f"Inference: {inf_time*1000:.1f} ms")
        self.info_roi_size.set(roi_text)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        now = time.time()
        fps = 1.0 / (now - self.last_frame_time)
        self.info_fps.set(f"True FPS: {fps:.2f}")
        self.last_frame_time = now

        delay = max(1.0 / self.max_fps.get() - (time.time() - now), 0)
        self.root.after(int(delay * 1000), self._process_frame)

    def on_mouse_move(self, event):
        if self.enable_roi.get():
            self.roi_center = (event.x, event.y)

    def on_mouse_wheel(self, event):
        if self.enable_roi.get():
            delta = 0
            if hasattr(event, "delta") and event.delta:
                delta = event.delta
            elif event.num == 4:
                delta = 120
            elif event.num == 5:
                delta = -120
            if delta > 0:
                self.roi_size += 20
            else:
                self.roi_size = max(20, self.roi_size - 20)

    def _load_cache(self):
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r") as f:
                    data = json.load(f)
                self.model_path.set(data.get("model", ""))
                self.video_path.set(data.get("video", ""))
            except Exception:
                pass

    def _save_cache(self):
        data = {"model": self.model_path.get(), "video": self.video_path.get()}
        try:
            with open(CACHE_PATH, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def on_close(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = VideoInferenceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
