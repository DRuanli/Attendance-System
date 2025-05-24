# app/utils/helpers.py
from datetime import datetime, time
import hashlib
import os
from typing import Optional


def generate_file_hash(file_path: str) -> str:
    """Generate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def is_within_class_time(class_start: time, class_end: time, current_time: Optional[datetime] = None) -> bool:
    """Check if current time is within class hours."""
    if current_time is None:
        current_time = datetime.now()

    current = current_time.time()

    # Handle case where class spans midnight
    if class_start <= class_end:
        return class_start <= current <= class_end
    else:
        return current >= class_start or current <= class_end


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        "data/student_photos",
        "data/encodings",
        "data/temp",
        "logs",
        "static/css",
        "static/js",
        "static/images"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)