# app/services/student_service.py
import cv2
import numpy as np
from typing import List, Optional, Dict
from app.core import FaceEncoder, FaceDetector
from app.utils.image_processing import load_and_preprocess_image
import logging

logger = logging.getLogger(__name__)


class StudentService:
    def __init__(self):
        self.encoder = FaceEncoder()
        self.detector = FaceDetector()

    async def generate_student_encoding(self, photo_paths: List[str]) -> Optional[bytes]:
        """Generate face encoding from multiple photos using FaceNet."""
        encodings = []

        for path in photo_paths:
            # Load and preprocess image
            image = load_and_preprocess_image(path)
            if image is None:
                continue

            # Detect and align faces
            aligned_faces, face_locations = self.detector.detect_and_align_faces(image)

            if not aligned_faces:
                logger.warning(f"No face detected in {path}")
                continue

            # Use the first (largest) face
            if len(aligned_faces) > 1:
                logger.warning(f"Multiple faces detected in {path}, using the first one")

            # Generate encoding
            encoding = self.encoder.generate_encoding(aligned_faces[0])
            if encoding is not None:
                encodings.append(encoding)
            else:
                logger.warning(f"Failed to generate encoding for {path}")

        if not encodings:
            return None

        # Average multiple encodings for better accuracy
        if len(encodings) > 1:
            # Stack encodings and compute mean
            stacked_encodings = np.stack(encodings)
            average_encoding = np.mean(stacked_encodings, axis=0)
            # Re-normalize the averaged encoding
            average_encoding = average_encoding / np.linalg.norm(average_encoding)
        else:
            average_encoding = encodings[0]

        logger.info(f"Generated encoding from {len(encodings)} photos")

        # Convert to bytes for storage
        return self.encoder.save_encoding_to_db(average_encoding)

    def update_student_photos(self, student_id: str, new_photo_paths: List[str]) -> Optional[bytes]:
        """Update student's face encoding with new photos."""
        return self.generate_student_encoding(new_photo_paths)

    def validate_photo_quality(self, photo_path: str) -> Dict[str, any]:
        """Validate photo quality for face recognition."""
        result = {
            "valid": False,
            "message": "",
            "face_count": 0,
            "quality_score": 0.0
        }

        image = load_and_preprocess_image(photo_path)
        if image is None:
            result["message"] = "Failed to load image"
            return result

        # Detect faces
        aligned_faces, face_locations = self.detector.detect_and_align_faces(image)

        if not aligned_faces:
            result["message"] = "No face detected"
            return result

        if len(aligned_faces) > 1:
            result["message"] = "Multiple faces detected"
            result["face_count"] = len(aligned_faces)
            return result

        # Check face size
        face = aligned_faces[0]
        if face.shape[0] < 80 or face.shape[1] < 80:
            result["message"] = "Face too small"
            return result

        # Calculate quality score based on sharpness
        gray = cv2.cvtColor(face, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        quality_score = min(laplacian_var / 100, 1.0)  # Normalize to 0-1

        result["valid"] = True
        result["message"] = "Photo is suitable for face recognition"
        result["face_count"] = 1
        result["quality_score"] = quality_score

        return result