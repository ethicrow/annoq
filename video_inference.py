import os
import json
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional dependency
    YOLO = None

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".annoq_video_cache.json")


class VideoInferenceApp:
    """Simple application to run video inference with optional ROI."""

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
        self.window_created = False

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

        tk.Button(control_frame, text="Start", command=self.start_playback).pack(fill=tk.X, pady=5)
        tk.Button(control_frame, text="Pause", command=self.pause_playback).pack(fill=tk.X, pady=5)
        tk.Button(control_frame, text="Rewind", command=self.rewind).pack(fill=tk.X, pady=5)
        tk.Button(control_frame, text="Forward", command=self.forward).pack(fill=tk.X, pady=5)

        info_frame = tk.LabelFrame(control_frame, text="Info")
        info_frame.pack(fill=tk.X, pady=5)
        tk.Label(info_frame, textvariable=self.info_roi_size).pack(anchor="w")
        tk.Label(info_frame, textvariable=self.info_inference).pack(anchor="w")
        tk.Label(info_frame, textvariable=self.info_fps).pack(anchor="w")

        if self.model_path.get() and os.path.exists(self.model_path.get()):
            self._load_model(self.model_path.get())
        if self.video_path.get() and os.path.exists(self.video_path.get()):
            self.cap = cv2.VideoCapture(self.video_path.get())

    def _ensure_window(self):
        if not self.window_created:
            cv2.namedWindow("Video")
            cv2.setMouseCallback("Video", self.on_mouse_event)
            self.window_created = True

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

    def start_playback(self):
        if not self.model:
            messagebox.showwarning("Warning", "Select a model first.")
            return
        if not self.cap:
            messagebox.showwarning("Warning", "Select a video first.")
            return
        self.running = True
        self.last_frame_time = time.time()
        self._ensure_window()
        self._process_frame()

    def pause_playback(self):
        self.running = False

    def rewind(self):
        if not self.cap:
            return
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        frames = int(fps * 5)
        pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, pos - frames))
        self._ensure_window()
        self._process_frame_once()

    def forward(self):
        if not self.cap:
            return
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        frames = int(fps * 5)
        pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        total = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, min(total - 1, pos + frames))
        self._ensure_window()
        self._process_frame_once()

    def _process_frame(self):
        if not self.running:
            return
        start = time.time()
        self._process_frame_once()
        if not self.running:
            return
        elapsed = time.time() - start
        delay = max(1.0 / self.max_fps.get() - elapsed, 0)
        self.root.after(int(delay * 1000), self._process_frame)

    def _process_frame_once(self):
        if not self.model or not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.running = False
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
            roi = frame[y1:y2, x1:x2].copy()
            results = self.model(roi)
            if results:
                roi_res = results[0].plot()
                if roi_res.shape[:2] != (y2 - y1, x2 - x1):
                    roi_res = cv2.resize(roi_res, (x2 - x1, y2 - y1))
                frame[y1:y2, x1:x2] = roi_res
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            roi_text = f"ROI size: {x2 - x1}x{y2 - y1}"
        else:
            results = self.model(frame)
            if results:
                frame = results[0].plot()

        inf_time = time.time() - start_time
        self.info_inference.set(f"Inference: {inf_time*1000:.1f} ms")
        self.info_roi_size.set(roi_text)

        now = time.time()
        fps = 1.0 / (now - self.last_frame_time)
        self.info_fps.set(f"True FPS: {fps:.2f}")
        self.last_frame_time = now

        self._ensure_window()
        cv2.imshow("Video", frame)
        cv2.waitKey(1)

    def on_mouse_event(self, event, x, y, flags, param):
        if self.enable_roi.get():
            if event == cv2.EVENT_MOUSEMOVE:
                self.roi_center = (x, y)
            elif event == cv2.EVENT_MOUSEWHEEL:
                if flags > 0:
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
        if self.window_created:
            cv2.destroyWindow("Video")
        self.root.destroy()


def main():
    root = tk.Tk()
    app = VideoInferenceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()

