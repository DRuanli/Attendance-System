# app/core/face_detection.py
import cv2
import numpy as np
from typing import List, Tuple, Optional
from facenet_pytorch import MTCNN
import torch
from PIL import Image


class FaceDetector:
    def __init__(self):
        # Use GPU if available
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

        # Initialize MTCNN for face detection
        self.detector = MTCNN(
            image_size=160,  # FaceNet input size
            margin=20,
            min_face_size=20,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=True,
            select_largest=False,
            keep_all=True,
            device=self.device
        )

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

        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_image)

        # Detect faces
        boxes, probs = self.detector.detect(pil_image)

        face_locations = []
        if boxes is not None:
            for box in boxes:
                # Convert from [x1, y1, x2, y2] to (top, right, bottom, left)
                x1, y1, x2, y2 = box.astype(int)
                face_locations.append((y1, x2, y2, x1))

        return face_locations

    def detect_and_align_faces(self, image: np.ndarray) -> Tuple[List[np.ndarray], List[Tuple[int, int, int, int]]]:
        """
        Detect and align faces for FaceNet input.
        Returns: (aligned_faces, face_locations)
        """
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image

        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_image)

        # Detect and align faces
        aligned_faces, probs, boxes = self.detector(pil_image, return_prob=True)

        face_locations = []
        aligned_face_arrays = []

        if aligned_faces is not None:
            for i, face in enumerate(aligned_faces):
                if face is not None:
                    # Convert tensor to numpy array
                    face_array = face.permute(1, 2, 0).cpu().numpy()
                    face_array = (face_array * 128 + 127.5).astype(np.uint8)
                    aligned_face_arrays.append(face_array)

                    # Convert box coordinates
                    if boxes is not None and i < len(boxes):
                        x1, y1, x2, y2 = boxes[i].astype(int)
                        face_locations.append((y1, x2, y2, x1))

        return aligned_face_arrays, face_locations

    def draw_face_boxes(self, image: np.ndarray, face_locations: List[Tuple],
                        names: Optional[List[str]] = None,
                        confidences: Optional[List[float]] = None) -> np.ndarray:
        """Draw bounding boxes around detected faces with optional names and confidence scores."""
        image_copy = image.copy()

        for i, (top, right, bottom, left) in enumerate(face_locations):
            # Draw rectangle
            color = (0, 255, 0) if names and names[i] != "Unknown" else (0, 0, 255)
            cv2.rectangle(image_copy, (left, top), (right, bottom), color, 2)

            # Prepare label
            label_parts = []
            if names and i < len(names):
                label_parts.append(names[i])
            if confidences and i < len(confidences) and names[i] != "Unknown":
                label_parts.append(f"{confidences[i]:.2f}")

            if label_parts:
                label = " - ".join(label_parts)
                # Draw label background
                cv2.rectangle(image_copy, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                # Draw text
                cv2.putText(image_copy, label, (left + 6, bottom - 6),
                            cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        return image_copy