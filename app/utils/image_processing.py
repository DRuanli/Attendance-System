# app/utils/image_processing.py
import cv2
import numpy as np
from typing import Optional, Tuple
import os


def load_and_preprocess_image(image_path: str, target_size: Tuple[int, int] = (640, 480)) -> Optional[np.ndarray]:
    """Load and preprocess image for face recognition."""
    if not os.path.exists(image_path):
        return None

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return None

    # Resize if too large
    height, width = image.shape[:2]
    if width > target_size[0] or height > target_size[1]:
        # Calculate aspect ratio
        aspect = width / height

        if aspect > target_size[0] / target_size[1]:
            new_width = target_size[0]
            new_height = int(new_width / aspect)
        else:
            new_height = target_size[1]
            new_width = int(new_height * aspect)

        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    # Enhance image quality
    image = enhance_image(image)

    return image


def enhance_image(image: np.ndarray) -> np.ndarray:
    """Enhance image for better face recognition."""
    # Convert to grayscale for processing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply histogram equalization
    equalized = cv2.equalizeHist(gray)

    # Apply bilateral filter to reduce noise while keeping edges sharp
    filtered = cv2.bilateralFilter(equalized, 9, 75, 75)

    # Convert back to BGR
    enhanced = cv2.cvtColor(filtered, cv2.COLOR_GRAY2BGR)

    # Adjust brightness and contrast
    alpha = 1.2  # Contrast control
    beta = 10  # Brightness control
    enhanced = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)

    return enhanced


def crop_face(image: np.ndarray, face_location: Tuple[int, int, int, int], padding: float = 0.2) -> np.ndarray:
    """Crop face from image with padding."""
    top, right, bottom, left = face_location

    height, width = image.shape[:2]

    # Add padding
    pad_h = int((bottom - top) * padding)
    pad_w = int((right - left) * padding)

    # Ensure bounds are within image
    top = max(0, top - pad_h)
    bottom = min(height, bottom + pad_h)
    left = max(0, left - pad_w)
    right = min(width, right + pad_w)

    return image[top:bottom, left:right]