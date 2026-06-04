"""ffmpeg helpers: extract mono audio, cut per-segment clips, concat."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("--- ffmpeg stderr ---")
        print(result.stderr)
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd[:3])}...")


def extract_audio_mono(video: Path, out_wav: Path, sr: int = 48000) -> None:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-i", str(video),
        "-vn", "-ac", "1", "-ar", str(sr), "-c:a", "pcm_s16le",
        str(out_wav),
    ])


def extract_segment(video: Path, start: float, end: float, out_mp4: Path,
                    fps: str | None = None) -> None:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}", "-i", str(video), "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
    ]
    # Lock output framerate to the A-cam's so each B segment has the same frame
    # count as its A counterpart. Without this, a B-cam at a different fps rounds
    # each segment to a different frame count and cumulative drift desyncs the
    # two reels by the end (e.g. 25fps B vs 23.976fps A drifts ~0.2s over 32 cuts).
    if fps:
        cmd += ["-r", fps]
    cmd.append(str(out_mp4))
    run(cmd)


def concat_segments(segments: list[Path], out_mp4: Path) -> None:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_mp4.parent / "concat_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in segments),
        encoding="utf-8",
    )
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(out_mp4),
    ])
    list_file.unlink(missing_ok=True)


def get_fps(video: Path) -> str:
    """Return the video stream's r_frame_rate as a string like '24000/1001'."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def get_duration(video: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())
