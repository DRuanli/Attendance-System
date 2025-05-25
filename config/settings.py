# config/settings.py
from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
import os


class Settings(BaseSettings):
    # App settings
    app_name: str = "Classroom Attendance System"
    debug: bool = True
    secret_key: str = "your-secret-key-here-change-in-production"

    # Database
    database_url: str = "sqlite:///./attendance.db"

    # Camera settings
    camera_index: int = 0  # Default USB camera
    frame_rate: int = 5
    enable_ip_cameras: bool = True
    camera_reconnect_attempts: int = 3
    camera_reconnect_delay: int = 5  # seconds

    # FaceNet Recognition settings
    similarity_threshold: float = 0.6  # Cosine similarity threshold (0.5-0.7 typical)
    confidence_threshold: float = 0.7  # Minimum confidence for positive match
    face_detection_confidence: float = 0.6  # MTCNN detection confidence
    min_face_size: int = 20  # Minimum face size for detection
    facenet_image_size: int = 160  # FaceNet input image size

    # Attendance tracking settings
    min_detections_required: int = 3  # Minimum detections before marking attendance
    track_timeout_seconds: int = 300  # 5 minutes - remove track if not seen
    min_tracking_duration: int = 10  # Minimum seconds of tracking before marking
    min_average_confidence: float = 0.7  # Minimum average confidence for attendance

    # Automatic scheduling
    enable_auto_scheduling: bool = True
    pre_class_start_minutes: int = 5  # Start attendance this many minutes before class
    post_class_end_minutes: int = 10  # End attendance this many minutes after class

    # Background service settings
    enable_background_service: bool = True
    service_health_check_interval: int = 30  # seconds

    # API settings
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # File storage
    upload_dir: str = "./data/student_photos"
    encodings_dir: str = "./data/encodings"
    temp_dir: str = "./data/temp"
    camera_config_file: str = "./config/camera_config.json"
    max_file_size: int = 5242880  # 5MB
    allowed_extensions: set = {".jpg", ".jpeg", ".png"}

    # Classroom settings
    late_threshold_minutes: int = 15

    # Notification settings (future feature)
    enable_notifications: bool = False
    notification_email: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.encodings_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("config", exist_ok=True)