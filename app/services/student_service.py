# app/services/student_service.py
import cv2
import numpy as np
from typing import List, Optional
from app.core import FaceEncoder
from app.utils.image_processing import load_and_preprocess_image
import logging

logger = logging.getLogger(__name__)


class StudentService:
    def __init__(self):
        self.encoder = FaceEncoder()

    async def generate_student_encoding(self, photo_paths: List[str]) -> Optional[bytes]:
        """Generate face encoding from multiple photos."""
        encodings = []

        for path in photo_paths:
            # Load and preprocess image
            image = load_and_preprocess_image(path)
            if image is None:
                continue

            # Generate encoding
            encoding = self.encoder.generate_encoding(image)
            if encoding is not None:
                encodings.append(encoding)

        if not encodings:
            return None

        # Average multiple encodings for better accuracy
        if len(encodings) > 1:
            average_encoding = np.mean(encodings, axis=0)
        else:
            average_encoding = encodings[0]

        # Convert to bytes for storage
        return self.encoder.save_encoding_to_db(average_encoding)

    def update_student_photos(self, student_id: str, new_photo_paths: List[str]) -> Optional[bytes]:
        """Update student's face encoding with new photos."""
        return self.generate_student_encoding(new_photo_paths)