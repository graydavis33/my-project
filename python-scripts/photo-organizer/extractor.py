"""
Photo Organizer — File Extractor + Thumbnail Generator
Finds photo files (including Canon CR3/CR2 RAW) and extracts
small JPEG thumbnails for vision analysis.
"""

import base64
import io
import os
from typing import Optional

import rawpy
import numpy as np
from PIL import Image


def find_photos(folder: str, extensions: set) -> list:
    """Recursively find all photo files in a folder."""
    photos = []
    for root, _, files in os.walk(folder):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in extensions:
                photos.append(os.path.join(root, name))
    return sorted(photos)


RAW_EXTENSIONS = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2"}


def _is_raw(filepath: str) -> bool:
    return os.path.splitext(filepath)[1].lower() in RAW_EXTENSIONS


def load_pil_image(filepath: str) -> Optional[Image.Image]:
    """
    Open a photo as a PIL Image regardless of format (JPEG, HEIC, RAW, etc.).
    Returns None if the file can't be read.
    """
    if _is_raw(filepath):
        try:
            with rawpy.imread(filepath) as raw:
                # Try to get embedded thumbnail first (fast, no demosaicing)
                try:
                    thumb = raw.extract_thumb()
                    if thumb.format == rawpy.ThumbFormat.JPEG:
                        return Image.open(io.BytesIO(thumb.data)).convert("RGB")
                    elif thumb.format == rawpy.ThumbFormat.BITMAP:
                        return Image.fromarray(thumb.data).convert("RGB")
                except rawpy.LibRawNoThumbnailError:
                    pass
                # Fall back to full RAW processing (slower but always works)
                rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=8)
                return Image.fromarray(rgb)
        except Exception:
            return None
    else:
        try:
            return Image.open(filepath).convert("RGB")
        except Exception:
            return None


def make_thumbnail_b64(filepath: str, max_px: int) -> Optional[str]:
    """
    Load photo, resize to max_px on longest side, return as base64 JPEG string.
    Used for sending to Claude vision API.
    Returns None if file can't be read.
    """
    img = load_pil_image(filepath)
    if img is None:
        return None

    # Resize keeping aspect ratio
    img.thumbnail((max_px, max_px), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def make_cv2_gray(filepath: str) -> Optional[np.ndarray]:
    """
    Load photo as grayscale numpy array for blur/quality scoring.
    Works with RAW and non-RAW files.
    """
    img = load_pil_image(filepath)
    if img is None:
        return None
    gray = img.convert("L")
    return np.array(gray)
