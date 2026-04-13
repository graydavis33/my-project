"""
Photo Organizer — Quality Scorer
Detects blurry photos and scores photo quality using local analysis only.
No AI API calls — runs fast even on 18,000 photos.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from PIL import Image

from config import (
    BLUR_THRESHOLD,
    WEIGHT_SHARPNESS,
    WEIGHT_EXPOSURE,
    WEIGHT_CONTRAST,
)


def load_image_gray(filepath: str) -> Optional[np.ndarray]:
    """Load image as grayscale numpy array. Returns None on failure."""
    try:
        img = cv2.imread(filepath)
        if img is None:
            # Fallback: use PIL for formats OpenCV can't read (HEIC, etc.)
            pil_img = Image.open(filepath).convert("L")
            return np.array(pil_img)
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    except Exception:
        return None


def laplacian_variance(gray: np.ndarray) -> float:
    """
    Measure sharpness via Laplacian variance.
    High value = sharp/in-focus. Low value = blurry.
    """
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(filepath: str) -> tuple[bool, float]:
    """
    Returns (is_blurry, blur_score).
    is_blurry=True means the photo should be rejected.
    """
    gray = load_image_gray(filepath)
    if gray is None:
        return True, 0.0   # Can't read = treat as blurry/bad
    score = laplacian_variance(gray)
    return score < BLUR_THRESHOLD, score


def exposure_score(gray: np.ndarray) -> float:
    """
    Score 0–1 based on how well-exposed the image is.
    Penalizes photos that are too dark (mean < 50) or too bright (mean > 205).
    """
    mean = float(gray.mean())
    if mean < 50:
        # Underexposed — scale 0→0.5 as mean goes 0→50
        return mean / 50.0 * 0.5
    elif mean > 205:
        # Overexposed — scale 0.5→0 as mean goes 205→255
        return (255 - mean) / 50.0 * 0.5
    else:
        # Well-exposed: score 0.5→1.0 based on proximity to ideal (128)
        distance_from_ideal = abs(mean - 128) / 77.0  # 77 = max distance in good range
        return 1.0 - (distance_from_ideal * 0.5)


def contrast_score(gray: np.ndarray) -> float:
    """
    Score 0–1 based on tonal range (standard deviation of pixel values).
    Higher std deviation = more contrast = better.
    """
    std = float(gray.std())
    # std of 60+ = great contrast, below 20 = very flat
    return min(std / 60.0, 1.0)


def quality_score(filepath: str, blur_score: float) -> float:
    """
    Compute a composite quality score (0–1) for a non-blurry photo.
    Combines sharpness, exposure, and contrast.
    """
    gray = load_image_gray(filepath)
    if gray is None:
        return 0.0

    # Normalize blur/sharpness score (cap at 500 for scoring — anything above is sharp)
    sharpness = min(blur_score / 500.0, 1.0)

    exposure = exposure_score(gray)
    contrast = contrast_score(gray)

    score = (
        WEIGHT_SHARPNESS * sharpness +
        WEIGHT_EXPOSURE  * exposure  +
        WEIGHT_CONTRAST  * contrast
    )
    return round(score, 4)
