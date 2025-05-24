# config/settings.py
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App settings
    app_name: str = "Classroom Attendance System"
    debug: bool = True
    secret_key: str = "your-secret-key-here-change-in-production"

    # Database
    database_url: str = "sqlite:///./attendance.db"

    # Camera settings
    camera_index: int = 0
    frame_rate: int = 5

    # FaceNet Recognition settings
    similarity_threshold: float = 0.6  # Cosine similarity threshold (0.5-0.7 typical)
    confidence_threshold: float = 0.7  # Minimum confidence for positive match
    face_detection_confidence: float = 0.6  # MTCNN detection confidence
    min_face_size: int = 20  # Minimum face size for detection
    facenet_image_size: int = 160  # FaceNet input image size

    # API settings
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # File storage
    upload_dir: str = "./data/student_photos"
    encodings_dir: str = "./data/encodings"
    temp_dir: str = "./data/temp"
    max_file_size: int = 5242880  # 5MB
    allowed_extensions: set = {".jpg", ".jpeg", ".png"}

    # Classroom settings
    late_threshold_minutes: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.encodings_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)
os.makedirs("logs", exist_ok=True)