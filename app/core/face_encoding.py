# app/core/face_encoding.py
import cv2
import numpy as np
import pickle
import os
import torch
from typing import List, Optional, Dict, Tuple
from facenet_pytorch import InceptionResnetV1
from PIL import Image
import torch.nn.functional as F
from config import settings


class FaceEncoder:
    def __init__(self):
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.encodings_dir = settings.encodings_dir

        # Load pre-trained FaceNet model
        self.model = InceptionResnetV1(
            pretrained='vggface2',
            classify=False,
            device=self.device
        ).eval()

        # Embedding size for FaceNet
        self.embedding_size = 512

    def preprocess_face(self, face_image: np.ndarray) -> torch.Tensor:
        """Preprocess face image for FaceNet input."""
        # Ensure image is RGB
        if len(face_image.shape) == 2:
            face_image = cv2.cvtColor(face_image, cv2.COLOR_GRAY2RGB)
        elif face_image.shape[2] == 4:
            face_image = cv2.cvtColor(face_image, cv2.COLOR_BGRA2RGB)

        # Resize to 160x160 (FaceNet input size)
        face_image = cv2.resize(face_image, (160, 160))

        # Convert to tensor and normalize
        face_tensor = torch.from_numpy(face_image).float()
        face_tensor = face_tensor.permute(2, 0, 1)  # HWC to CHW

        # Normalize to [-1, 1]
        face_tensor = (face_tensor - 127.5) / 128.0

        return face_tensor.unsqueeze(0).to(self.device)

    def generate_encoding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Generate face encoding using FaceNet."""
        try:
            # Preprocess face
            face_tensor = self.preprocess_face(face_image)

            # Generate embedding
            with torch.no_grad():
                embedding = self.model(face_tensor)

            # Convert to numpy array
            embedding_np = embedding.cpu().numpy().flatten()

            # L2 normalize the embedding
            embedding_np = embedding_np / np.linalg.norm(embedding_np)

            return embedding_np

        except Exception as e:
            print(f"Error generating encoding: {e}")
            return None

    def generate_encoding_batch(self, face_images: List[np.ndarray]) -> List[Optional[np.ndarray]]:
        """Generate encodings for multiple faces efficiently."""
        if not face_images:
            return []

        try:
            # Preprocess all faces
            face_tensors = []
            for face in face_images:
                face_tensor = self.preprocess_face(face)
                face_tensors.append(face_tensor)

            # Stack tensors for batch processing
            batch_tensor = torch.cat(face_tensors, dim=0)

            # Generate embeddings
            with torch.no_grad():
                embeddings = self.model(batch_tensor)

            # Convert to numpy and normalize
            embeddings_np = embeddings.cpu().numpy()
            normalized_embeddings = []

            for embedding in embeddings_np:
                normalized = embedding / np.linalg.norm(embedding)
                normalized_embeddings.append(normalized)

            return normalized_embeddings

        except Exception as e:
            print(f"Error in batch encoding: {e}")
            return [None] * len(face_images)

    def save_encoding(self, student_id: str, encoding: np.ndarray) -> str:
        """Save encoding to file."""
        filename = f"{student_id}_facenet_encoding.pkl"
        filepath = os.path.join(self.encodings_dir, filename)

        encoding_data = {
            'encoding': encoding,
            'model': 'facenet',
            'embedding_size': self.embedding_size
        }

        with open(filepath, 'wb') as f:
            pickle.dump(encoding_data, f)

        return filepath

    def load_encoding(self, student_id: str) -> Optional[np.ndarray]:
        """Load encoding from file."""
        filename = f"{student_id}_facenet_encoding.pkl"
        filepath = os.path.join(self.encodings_dir, filename)

        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                return data['encoding']
        return None

    def save_encoding_to_db(self, encoding: np.ndarray) -> bytes:
        """Convert encoding to bytes for database storage."""
        encoding_data = {
            'encoding': encoding,
            'model': 'facenet',
            'embedding_size': self.embedding_size
        }
        return pickle.dumps(encoding_data)

    def load_encoding_from_db(self, encoding_bytes: bytes) -> np.ndarray:
        """Load encoding from database bytes."""
        data = pickle.loads(encoding_bytes)
        return data['encoding']

    def compute_similarity(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Compute cosine similarity between two encodings."""
        # Both encodings should already be L2 normalized
        similarity = np.dot(encoding1, encoding2)
        return float(similarity)

    def compute_distance(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Compute Euclidean distance between two encodings."""
        return float(np.linalg.norm(encoding1 - encoding2))