# app/core/camera_handler.py
import cv2
import threading
import queue
import time
from typing import Optional, Callable
import logging
from config import settings
import numpy as np

logger = logging.getLogger(__name__)


class CameraHandler:
    def __init__(self, camera_index: int = None):
        self.camera_index = camera_index or settings.camera_index
        self.cap = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.capture_thread = None
        self.frame_rate = settings.frame_rate
        self.frame_interval = 1.0 / self.frame_rate

    def start(self):
        """Start camera capture."""
        if self.is_running:
            return

        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera {self.camera_index}")

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)

        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        logger.info(f"Camera {self.camera_index} started")

    def stop(self):
        """Stop camera capture."""
        self.is_running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

        if self.cap:
            self.cap.release()
            self.cap = None

        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        logger.info(f"Camera {self.camera_index} stopped")

    def _capture_loop(self):
        """Continuous capture loop running in separate thread."""
        last_capture_time = 0

        while self.is_running:
            current_time = time.time()

            # Control frame rate
            if current_time - last_capture_time < self.frame_interval:
                time.sleep(0.01)
                continue

            ret, frame = self.cap.read()
            if ret:
                # Add frame to queue (drop old frames if queue is full)
                try:
                    self.frame_queue.put_nowait(frame)
                    last_capture_time = current_time
                except queue.Full:
                    # Remove old frame and add new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
            else:
                logger.error("Failed to capture frame")
                time.sleep(0.1)

    def get_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get the latest frame from the camera."""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def capture_single_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame directly."""
        if not self.cap or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)

        ret, frame = self.cap.read()
        return frame if ret else None