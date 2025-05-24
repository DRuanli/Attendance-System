# app/core/face_detection.py
import cv2
import face_recognition
import numpy as np
from typing import List, Tuple, Optional
from config import settings


class FaceDetector:
    def __init__(self):
        self.model = settings.face_detection_model
        self.upsample_times = settings.number_of_times_to_upsample

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in an image and return their locations.
        Returns: List of (top, right, bottom, left) tuples
        """
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image

        # Detect faces
        face_locations = face_recognition.face_locations(
            rgb_image,
            number_of_times_to_upsample=self.upsample_times,
            model=self.model
        )

        return face_locations

    def draw_face_boxes(self, image: np.ndarray, face_locations: List[Tuple],
                        names: Optional[List[str]] = None) -> np.ndarray:
        """Draw bounding boxes around detected faces with optional names."""
        image_copy = image.copy()

        for i, (top, right, bottom, left) in enumerate(face_locations):
            # Draw rectangle
            cv2.rectangle(image_copy, (left, top), (right, bottom), (0, 255, 0), 2)

            # Add name label if provided
            if names and i < len(names):
                name = names[i]
                # Draw label background
                cv2.rectangle(image_copy, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                # Draw text
                cv2.putText(image_copy, name, (left + 6, bottom - 6),
                            cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        return image_copy