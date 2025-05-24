# app/utils/validators.py
from fastapi import UploadFile
import os
from typing import Optional
from config import settings


def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file."""
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.allowed_extensions:
        return False

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.max_file_size:
        return False

    # Check MIME type
    if not file.content_type.startswith('image/'):
        return False

    return True


def validate_student_id(student_id: str) -> bool:
    """Validate student ID format."""
    # Add your student ID validation logic
    if not student_id:
        return False

    # Example: Student ID should be alphanumeric and 6-10 characters
    if not student_id.isalnum():
        return False

    if not 6 <= len(student_id) <= 10:
        return False

    return True


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None