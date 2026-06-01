"""
extractor.py
Uses ffprobe to get video duration, then ffmpeg to extract 4 frames as base64 JPEGs.
"""
import base64
import os
import shutil
import subprocess
import tempfile

from config import FRAME_POSITIONS


def get_shoot_date(filepath: str) -> str:
    """
    Read the shoot date from camera-embedded metadata via ffprobe.
    Returns a 'YYYY-MM-DD' string.
    Falls back to the file's last-modified date if metadata is missing.
    """
    import json
    from datetime import datetime, timezone

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_entries", "format_tags=creation_time",
        filepath,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        creation_time = data.get("format", {}).get("tags", {}).get("creation_time", "")
        if creation_time:
            # Format: "2026-04-16T14:23:45.000000Z"
            dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
            return dt.astimezone().strftime("%Y-%m-%d")
    except Exception:
        pass

    # Fallback: file modification time
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def get_resolution(filepath: str) -> tuple[int, int]:
    """
    Get video width and height via ffprobe.
    Returns (width, height). Raises RuntimeError if it fails.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        filepath,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    raw = result.stdout.strip()
    try:
        parts = raw.split(",")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        raise RuntimeError(f"Could not parse resolution from ffprobe: '{raw}'")


def get_duration(filepath: str) -> float:
    """
    Get video duration in seconds via ffprobe.
    Raises RuntimeError if ffprobe fails or output can't be parsed.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    raw = result.stdout.strip()
    try:
        return float(raw)
    except ValueError:
        raise RuntimeError(f"Could not parse duration from ffprobe: '{raw}'")


def extract_frames(filepath: str, duration: float) -> list[str]:
    """
    Extract one JPEG frame at each FRAME_POSITIONS percentage through the video.
    Returns a list of base64-encoded JPEG strings (one per position).

    -ss before -i = fast seek (keyframe-accurate, ~10x faster for long files)
    -frames:v 1   = extract exactly one frame
    -q:v 3        = JPEG quality (2=best, 5=smaller); 3 is a solid balance
    """
    frames_b64 = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, position in enumerate(FRAME_POSITIONS):
            seek_time = duration * position
            out_path = os.path.join(tmpdir, f"frame_{i}.jpg")

            cmd = [
                "ffmpeg",
                "-ss", f"{seek_time:.3f}",
                "-i", filepath,
                "-frames:v", "1",
                "-q:v", "3",
                "-y",
                out_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True)

            with open(out_path, "rb") as f:
                frames_b64.append(base64.b64encode(f.read()).decode("utf-8"))

    return frames_b64
