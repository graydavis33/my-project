"""
Photo Organizer — Quality Scorer
Detects blurry photos and scores quality using local analysis only.
No AI API calls — fast even on large batches.

NOTE: Exposure is intentionally excluded from scoring.
The shooter uses Canon RAW (CR3) and deliberately underexposes to recover
highlights in post. Penalizing dark frames would cut the best shots.
"""

import cv2
import numpy as np
from typing import Optional

from config import BLUR_THRESHOLD, WEIGHT_SHARPNESS, WEIGHT_CONTRAST
from extractor import make_cv2_gray


def load_image_gray(filepath: str) -> Optional[np.ndarray]:
    """Load photo as grayscale numpy array (handles CR3/RAW + JPEG). Returns None on failure."""
    return make_cv2_gray(filepath)


def laplacian_variance(gray: np.ndarray) -> float:
    """
    Measure sharpness via Laplacian variance.
    High = sharp/in-focus. Low = blurry.
    """
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(filepath: str) -> tuple:
    """
    Returns (is_blurry: bool, blur_score: float).
    is_blurry=True means reject immediately.
    """
    gray = load_image_gray(filepath)
    if gray is None:
        return True, 0.0
    score = laplacian_variance(gray)
    return score < BLUR_THRESHOLD, score


def contrast_score(gray: np.ndarray) -> float:
    """
    Score 0–1 based on tonal range (std deviation of pixel values).
    Higher = more contrast = better.
    """
    std = float(gray.std())
    return min(std / 60.0, 1.0)


def quality_score(filepath: str, blur_score: float) -> float:
    """
    Composite quality score (0–1) for a non-blurry photo.
    Sharpness (80%) + Contrast (20%). No exposure penalty.
    """
    gray = load_image_gray(filepath)
    if gray is None:
        return 0.0

    sharpness = min(blur_score / 500.0, 1.0)
    contrast  = contrast_score(gray)

    return round(WEIGHT_SHARPNESS * sharpness + WEIGHT_CONTRAST * contrast, 4)
