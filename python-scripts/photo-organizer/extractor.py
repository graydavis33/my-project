"""
Photo Organizer — EXIF Extractor
Reads GPS coordinates and basic metadata from photo files.
"""

import os
import struct
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def get_exif(filepath: str) -> dict:
    """Return raw EXIF data dict from a photo, or empty dict if none."""
    try:
        img = Image.open(filepath)
        raw = img._getexif()
        if not raw:
            return {}
        return {TAGS.get(tag, tag): value for tag, value in raw.items()}
    except Exception:
        return {}


def get_gps_coords(filepath: str) -> Optional[Tuple[float, float]]:
    """
    Return (latitude, longitude) decimal degrees from photo EXIF, or None.
    """
    exif = get_exif(filepath)
    gps_info_raw = exif.get("GPSInfo")
    if not gps_info_raw:
        return None

    # Convert raw GPSInfo tag numbers to named keys
    gps = {}
    for key, val in gps_info_raw.items():
        name = GPSTAGS.get(key, key)
        gps[name] = val

    try:
        lat  = _dms_to_decimal(gps["GPSLatitude"],  gps.get("GPSLatitudeRef",  "N"))
        lon  = _dms_to_decimal(gps["GPSLongitude"], gps.get("GPSLongitudeRef", "E"))
        return (lat, lon)
    except (KeyError, TypeError, ZeroDivisionError):
        return None


def get_date_taken(filepath: str) -> Optional[datetime]:
    """Return date photo was taken from EXIF, or None."""
    exif = get_exif(filepath)
    raw = exif.get("DateTimeOriginal") or exif.get("DateTime")
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _dms_to_decimal(dms, ref: str) -> float:
    """Convert degrees/minutes/seconds tuple to decimal degrees."""
    def to_float(val):
        if isinstance(val, tuple):
            return val[0] / val[1] if val[1] != 0 else 0.0
        return float(val)

    degrees = to_float(dms[0])
    minutes = to_float(dms[1])
    seconds = to_float(dms[2])
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def find_photos(folder: str, extensions: set) -> list[str]:
    """Recursively find all photo files in a folder."""
    photos = []
    for root, _, files in os.walk(folder):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in extensions:
                photos.append(os.path.join(root, name))
    return sorted(photos)
