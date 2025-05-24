# app/core/face_encoding.py
import cv2
import face_recognition
import numpy as np
import pickle
import os
from typing import List, Optional, Dict, Tuple
from config import settings


class FaceEncoder:
    def __init__(self):
        self.encoding_model = settings.face_encoding_model
        self.encodings_dir = settings.encodings_dir

    def generate_encoding(self, image: np.ndarray, face_location: Optional[Tuple] = None) -> Optional[np.ndarray]:
        """Generate face encoding from image."""
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image

        # Get face encodings
        if face_location:
            face_encodings = face_recognition.face_encodings(
                rgb_image,
                known_face_locations=[face_location],
                model=self.encoding_model
            )
        else:
            face_encodings = face_recognition.face_encodings(rgb_image, model=self.encoding_model)

        return face_encodings[0] if face_encodings else None

    def save_encoding(self, student_id: str, encoding: np.ndarray) -> str:
        """Save encoding to file."""
        filename = f"{student_id}_encoding.pkl"
        filepath = os.path.join(self.encodings_dir, filename)

        with open(filepath, 'wb') as f:
            pickle.dump(encoding, f)

        return filepath

    def load_encoding(self, student_id: str) -> Optional[np.ndarray]:
        """Load encoding from file."""
        filename = f"{student_id}_encoding.pkl"
        filepath = os.path.join(self.encodings_dir, filename)

        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        return None

    def save_encoding_to_db(self, encoding: np.ndarray) -> bytes:
        """Convert encoding to bytes for database storage."""
        return pickle.dumps(encoding)

    def load_encoding_from_db(self, encoding_bytes: bytes) -> np.ndarray:
        """Load encoding from database bytes."""
        return pickle.loads(encoding_bytes)