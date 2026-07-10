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


def get_display_orientation(filepath: str) -> tuple[str, bool]:
    """Return (orientation, flipped) where orientation is 'horizontal' | 'vertical'
    | 'square' | 'unknown' and flipped is True when a rotation flag changed the
    orientation vs the stored dimensions.

    Sony often records 1920x1080 (stored landscape) + a 90/270 rotation flag, so
    it DISPLAYS vertical. Trusting width/height alone mislabels those — so we read
    the rotation (stream tag `rotate` or side-data Display Matrix `rotation`) and
    swap accordingly. `flipped=True` marks the tricky ones worth a human spot-check.
    """
    import json
    # Use stream_side_data (Display Matrix) — `side_data` without the `stream_`
    # prefix forces ffprobe to read packets (~5s/file); stream_side_data reads
    # the header only (~0.08s). stream_tags=rotate covers older clips. Per-file
    # timeout so one corrupt clip can't stall a whole-library pass (→ "unknown").
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:stream_tags=rotate:stream_side_data=rotation",
        "-of", "json", filepath,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=20)
        streams = json.loads(result.stdout or "{}").get("streams", [])
    except Exception:
        return ("unknown", False)
    if not streams:
        return ("unknown", False)
    return _orientation_from_stream(streams[0])


def _orientation_from_stream(s: dict) -> tuple[str, bool]:
    """(orientation, flipped) from one ffprobe video-stream dict — the shared
    rotation math behind get_display_orientation and probe_media."""
    w, h = int(s.get("width") or 0), int(s.get("height") or 0)
    if not w or not h:
        return ("unknown", False)

    rot = 0
    tag_rot = (s.get("tags") or {}).get("rotate")
    if tag_rot is not None:
        try:
            rot = int(tag_rot)
        except (TypeError, ValueError):
            rot = 0
    for sd in (s.get("side_data_list") or []):
        if "rotation" in sd:
            try:
                rot = int(sd["rotation"])
            except (TypeError, ValueError):
                pass
            break
    rot = abs(rot) % 180  # 0 or 90 is all that matters for orientation
    dw, dh = (h, w) if rot == 90 else (w, h)

    def _orient(a, b):
        return "vertical" if b > a else ("horizontal" if a > b else "square")

    display = _orient(dw, dh)
    stored = _orient(w, h)
    return (display, display != stored)


def probe_media(filepath: str) -> dict:
    """Everything the indexer needs from ONE ffprobe launch: width, height,
    duration_s, filmed_date, orientation. Replaces four separate subprocess
    spawns per clip (resolution / duration / shoot date / orientation) — the
    header-only read is ~5x faster and the fork overhead drops 4x.
    Raises RuntimeError when the file has no probeable video stream."""
    import json
    from datetime import datetime

    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries",
        "stream=width,height:stream_tags=rotate:stream_side_data=rotation:"
        "format=duration:format_tags=creation_time",
        "-of", "json", str(filepath),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=20)
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams") or []
    if not streams:
        raise RuntimeError("no video stream")
    s = streams[0]
    w, h = int(s.get("width") or 0), int(s.get("height") or 0)
    if not w or not h:
        raise RuntimeError("could not read resolution")

    fmt = data.get("format") or {}
    try:
        duration = float(fmt.get("duration"))
    except (TypeError, ValueError):
        raise RuntimeError(f"could not parse duration: '{fmt.get('duration')}'")

    filmed = None
    creation_time = (fmt.get("tags") or {}).get("creation_time", "")
    if creation_time:
        try:
            dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
            filmed = dt.astimezone().strftime("%Y-%m-%d")
        except ValueError:
            pass
    if filmed is None:
        # Same fallback as get_shoot_date: file modification time.
        filmed = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d")

    return {
        "width": w,
        "height": h,
        "duration_s": duration,
        "filmed_date": filmed,
        "orientation": _orientation_from_stream(s)[0],
    }


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
