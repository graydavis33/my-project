"""
video_cutter.py
Uses ffmpeg to cut clips from the original video file.
Silently skips cutting if ffmpeg is not installed or timestamps are null.
"""

import os
import shutil
import subprocess
from config import OUTPUT_DIR


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def cut_clip(video_path: str, clip: dict, output_name: str) -> str | None:
    """
    Cut a clip from video_path using ffmpeg.
    Returns the output path, or None if cutting failed/skipped.
    """
    start = clip.get("start_time")
    end = clip.get("end_time")

    if start is None or end is None:
        return None  # No timestamps available

    if not _ffmpeg_available():
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{output_name}.mp4")
    duration = end - start

    cmd = [
        "ffmpeg",
        "-y",                    # overwrite
        "-ss", str(start),       # start time (fast seek)
        "-i", video_path,        # input
        "-t", str(duration),     # duration
        "-c:v", "libx264",       # re-encode video (ensures compatibility)
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",            # quality (18=best, 28=smallest)
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  ffmpeg failed for {output_name}: {e.stderr.decode()[:200]}")
        return None


def cut_all_clips(video_path: str, clips: list, base_name: str) -> list:
    """
    Cut all clips from video. Returns list of output paths (None if skipped).
    """
    if not _ffmpeg_available():
        print("  ⚠️  ffmpeg not found — skipping video cuts. Install ffmpeg to enable auto-cutting.")
        return [None] * len(clips)

    results = []
    for clip in clips:
        clip_name = f"{base_name}_clip{clip.get('clip_number', '?')}"
        print(f"  Cutting: {clip_name} ({clip.get('start_time')}s – {clip.get('end_time')}s)...")
        path = cut_clip(video_path, clip, clip_name)
        if path:
            print(f"    ✓ Saved: {path}")
        results.append(path)
    return results
