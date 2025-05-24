# app/core/face_recognition.py
import face_recognition
import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional
from datetime import datetime
import logging
from config import settings
from .face_detection import FaceDetector
from .face_encoding import FaceEncoder

logger = logging.getLogger(__name__)


class FaceRecognitionSystem:
    def __init__(self):
        self.detector = FaceDetector()
        self.encoder = FaceEncoder()
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []
        self.known_face_ids: List[int] = []
        self.threshold = settings.recognition_threshold
        self.confidence_threshold = settings.confidence_threshold

    def load_known_faces(self, students: List[Dict]):
        """Load known faces from database."""
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []

        for student in students:
            if student.get('face_encoding'):
                encoding = self.encoder.load_encoding_from_db(student['face_encoding'])
                self.known_face_encodings.append(encoding)
                self.known_face_names.append(student['full_name'])
                self.known_face_ids.append(student['id'])

        logger.info(f"Loaded {len(self.known_face_encodings)} known faces")

    def recognize_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Recognize faces in an image.
        Returns: List of dicts with face info (name, id, location, confidence)
        """
        # Detect faces
        face_locations = self.detector.detect_faces(image)

        if not face_locations:
            return []

        # Get encodings for detected faces
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        results = []

        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.known_face_encodings,
                face_encoding,
                tolerance=self.threshold
            )

            name = "Unknown"
            student_id = None
            confidence = 0.0

            if True in matches:
                # Find best match
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    confidence = 1.0 - face_distances[best_match_index]

                    if confidence >= self.confidence_threshold:
                        name = self.known_face_names[best_match_index]
                        student_id = self.known_face_ids[best_match_index]

            results.append({
                'name': name,
                'student_id': student_id,
                'location': face_location,
                'confidence': float(confidence),
                'timestamp': datetime.now()
            })

        return results

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """Process a single frame and return annotated image with recognition results."""
        # Recognize faces
        results = self.recognize_faces(frame)

        # Draw boxes and labels
        names = [r['name'] for r in results]
        locations = [r['location'] for r in results]
        annotated_frame = self.detector.draw_face_boxes(frame, locations, names)

        return annotated_frame, results