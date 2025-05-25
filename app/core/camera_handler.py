# app/core/camera_handler.py
import cv2
import threading
import queue
import time
from typing import Optional, List, Dict, Union
import logging
from config import settings
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CameraType(Enum):
    USB = "usb"
    IP = "ip"
    RTSP = "rtsp"


@dataclass
class CameraConfig:
    camera_id: Union[int, str]
    camera_type: CameraType
    name: str
    location: str
    username: Optional[str] = None
    password: Optional[str] = None
    fps: int = 5
    resolution: tuple = (640, 480)
    reconnect_attempts: int = 3


class MultiCameraHandler:
    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        self.is_running = False
        self.frame_processors = []

    def add_camera(self, config: CameraConfig) -> str:
        """Add a camera to the handler."""
        camera_key = f"{config.name}_{config.location}"

        if camera_key in self.cameras:
            logger.warning(f"Camera {camera_key} already exists")
            return camera_key

        camera = CameraStream(config)
        self.cameras[camera_key] = camera

        if self.is_running:
            camera.start()

        logger.info(f"Added camera: {camera_key}")
        return camera_key

    def remove_camera(self, camera_key: str):
        """Remove a camera from the handler."""
        if camera_key in self.cameras:
            self.cameras[camera_key].stop()
            del self.cameras[camera_key]
            logger.info(f"Removed camera: {camera_key}")

    def start_all(self):
        """Start all cameras."""
        self.is_running = True
        for camera in self.cameras.values():
            camera.start()

    def stop_all(self):
        """Stop all cameras."""
        self.is_running = False
        for camera in self.cameras.values():
            camera.stop()

    def get_frame(self, camera_key: str) -> Optional[np.ndarray]:
        """Get latest frame from specific camera."""
        if camera_key in self.cameras:
            return self.cameras[camera_key].get_frame()
        return None

    def get_all_frames(self) -> Dict[str, np.ndarray]:
        """Get latest frames from all cameras."""
        frames = {}
        for key, camera in self.cameras.items():
            frame = camera.get_frame()
            if frame is not None:
                frames[key] = frame
        return frames


class CameraStream:
    def __init__(self, config: CameraConfig):
        self.config = config
        self.cap = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.capture_thread = None
        self.reconnect_thread = None
        self.last_frame_time = 0
        self.frame_interval = 1.0 / config.fps
        self.connection_lost = False

    def _get_stream_url(self) -> Union[int, str]:
        """Get the appropriate stream URL based on camera type."""
        if self.config.camera_type == CameraType.USB:
            return int(self.config.camera_id)
        elif self.config.camera_type == CameraType.IP:
            # Format: http://username:password@ip:port/video
            if self.config.username and self.config.password:
                return f"http://{self.config.username}:{self.config.password}@{self.config.camera_id}/video"
            return f"http://{self.config.camera_id}/video"
        elif self.config.camera_type == CameraType.RTSP:
            # Format: rtsp://username:password@ip:port/stream
            if self.config.username and self.config.password:
                return f"rtsp://{self.config.username}:{self.config.password}@{self.config.camera_id}"
            return f"rtsp://{self.config.camera_id}"

    def _initialize_capture(self) -> bool:
        """Initialize video capture with appropriate settings."""
        try:
            stream_url = self._get_stream_url()

            if self.config.camera_type in [CameraType.IP, CameraType.RTSP]:
                # Set buffer size for network streams
                self.cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            else:
                self.cap = cv2.VideoCapture(stream_url)

            if not self.cap.isOpened():
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

            # For network streams, reduce latency
            if self.config.camera_type in [CameraType.IP, CameraType.RTSP]:
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

            return True

        except Exception as e:
            logger.error(f"Failed to initialize camera {self.config.name}: {e}")
            return False

    def start(self):
        """Start camera capture."""
        if self.is_running:
            return

        if not self._initialize_capture():
            logger.error(f"Cannot start camera {self.config.name}")
            return

        self.is_running = True
        self.connection_lost = False

        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        logger.info(f"Started camera: {self.config.name}")

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

        logger.info(f"Stopped camera: {self.config.name}")

    def _capture_loop(self):
        """Continuous capture loop with reconnection logic."""
        consecutive_failures = 0

        while self.is_running:
            current_time = time.time()

            # Control frame rate
            if current_time - self.last_frame_time < self.frame_interval:
                time.sleep(0.01)
                continue

            if not self.cap or not self.cap.isOpened():
                if not self._reconnect():
                    time.sleep(1)
                    continue

            ret, frame = self.cap.read()

            if ret and frame is not None:
                consecutive_failures = 0
                self.connection_lost = False

                # Add frame to queue
                try:
                    self.frame_queue.put_nowait(frame)
                    self.last_frame_time = current_time
                except queue.Full:
                    # Remove old frame and add new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
            else:
                consecutive_failures += 1

                if consecutive_failures > 10:
                    logger.warning(f"Lost connection to camera {self.config.name}")
                    self.connection_lost = True

                    if self.cap:
                        self.cap.release()
                        self.cap = None

                    time.sleep(1)

    def _reconnect(self) -> bool:
        """Attempt to reconnect to camera."""
        if not self.is_running:
            return False

        logger.info(f"Attempting to reconnect to camera {self.config.name}")

        for attempt in range(self.config.reconnect_attempts):
            if self._initialize_capture():
                logger.info(f"Reconnected to camera {self.config.name}")
                return True

            time.sleep(2 ** attempt)  # Exponential backoff

        logger.error(f"Failed to reconnect to camera {self.config.name}")
        return False

    def get_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get the latest frame from the camera."""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def is_connected(self) -> bool:
        """Check if camera is connected and working."""
        return self.is_running and not self.connection_lost