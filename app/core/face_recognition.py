# app/core/face_recognition.py
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

        # FaceNet uses cosine similarity, so we use different thresholds
        self.similarity_threshold = 0.6  # Cosine similarity threshold
        self.confidence_threshold = 0.7  # Minimum confidence for positive match

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
        Recognize faces in an image using FaceNet.
        Returns: List of dicts with face info (name, id, location, confidence)
        """
        # Detect and align faces
        aligned_faces, face_locations = self.detector.detect_and_align_faces(image)

        if not aligned_faces:
            return []

        # Generate encodings for detected faces
        face_encodings = []
        for aligned_face in aligned_faces:
            encoding = self.encoder.generate_encoding(aligned_face)
            if encoding is not None:
                face_encodings.append(encoding)

        results = []

        for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
            name = "Unknown"
            student_id = None
            best_similarity = 0.0

            if len(self.known_face_encodings) > 0:
                # Compute similarities with all known faces
                similarities = []
                for known_encoding in self.known_face_encodings:
                    similarity = self.encoder.compute_similarity(face_encoding, known_encoding)
                    similarities.append(similarity)

                # Find best match
                best_match_index = np.argmax(similarities)
                best_similarity = similarities[best_match_index]

                # Check if similarity exceeds threshold
                if best_similarity >= self.similarity_threshold:
                    name = self.known_face_names[best_match_index]
                    student_id = self.known_face_ids[best_match_index]

                    # Additional verification with distance metric
                    distance = self.encoder.compute_distance(
                        face_encoding,
                        self.known_face_encodings[best_match_index]
                    )

                    # FaceNet typically uses distance threshold around 1.0-1.2
                    if distance > 1.2:
                        name = "Unknown"
                        student_id = None
                        best_similarity = 0.0

            results.append({
                'name': name,
                'student_id': student_id,
                'location': face_location,
                'confidence': float(best_similarity),
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
        confidences = [r['confidence'] for r in results]

        annotated_frame = self.detector.draw_face_boxes(
            frame, locations, names, confidences
        )

        return annotated_frame, results

    def verify_face(self, face_image: np.ndarray, student_id: int) -> Tuple[bool, float]:
        """
        Verify if a face matches a specific student.
        Returns: (is_match, confidence)
        """
        # Generate encoding for the face
        face_encoding = self.encoder.generate_encoding(face_image)
        if face_encoding is None:
            return False, 0.0

        # Find the student's encoding
        try:
            student_index = self.known_face_ids.index(student_id)
            known_encoding = self.known_face_encodings[student_index]

            # Compute similarity
            similarity = self.encoder.compute_similarity(face_encoding, known_encoding)

            # Check if it's a match
            is_match = similarity >= self.similarity_threshold

            return is_match, float(similarity)

        except ValueError:
            # Student not found in known faces
            return False, 0.0