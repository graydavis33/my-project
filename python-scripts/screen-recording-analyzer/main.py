"""
screen-recording-analyzer

Takes a screen recording and produces an analysis bundle that an AI agent can read:
  - frames/       scene-change frames (or every N seconds) as JPGs
  - transcript.md audio transcript with timestamps
  - manifest.json index of frames + timestamps + video metadata

Run:
    python main.py path/to/video.mp4
    python main.py path/to/video.mp4 --interval 5         # every 5s instead of scene-change
    python main.py path/to/video.mp4 --out custom/output  # custom output folder
"""

import argparse
import json
import os
import subprocess
import sys
import shutil
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def run(cmd: list, capture=False):
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return subprocess.run(cmd)


def probe_duration(video_path: str) -> float:
    result = run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def extract_frames_scene(video_path: str, out_dir: Path, threshold: float = 0.3) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(out_dir / "frame_%05d.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr", "-q:v", "3", pattern,
    ]
    result = run(cmd, capture=True)
    timestamps = []
    for line in result.stderr.splitlines():
        if "pts_time:" in line:
            try:
                ts = float(line.split("pts_time:")[1].split()[0])
                timestamps.append(round(ts, 2))
            except (IndexError, ValueError):
                continue
    frames = sorted(out_dir.glob("frame_*.jpg"))
    pairs = list(zip([f.name for f in frames], timestamps[: len(frames)]))
    return pairs


def extract_frames_interval(video_path: str, out_dir: Path, interval: int) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(out_dir / "frame_%05d.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"fps=1/{interval}",
        "-q:v", "3", pattern,
    ]
    run(cmd, capture=True)
    frames = sorted(out_dir.glob("frame_*.jpg"))
    return [(f.name, round(i * interval, 2)) for i, f in enumerate(frames)]


def transcribe_local_whisper(video_path: str, model_name: str = "large-v3") -> list:
    try:
        import whisper
    except ImportError:
        print("  openai-whisper not installed. Run: pip install openai-whisper")
        return []
    print(f"  Transcribing with local Whisper ({model_name})...")
    model = whisper.load_model(model_name)
    result = model.transcribe(video_path, verbose=False)
    return [
        {"start": round(s["start"], 1), "end": round(s["end"], 1), "text": s["text"].strip()}
        for s in result.get("segments", [])
    ]


def write_transcript_md(segments: list, path: Path):
    lines = ["# Transcript\n"]
    for seg in segments:
        m, s = divmod(int(seg["start"]), 60)
        lines.append(f"**[{m:02d}:{s:02d}]** {seg['text']}")
    path.write_text("\n\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Extract frames + transcript from a screen recording.")
    parser.add_argument("video", help="Path to the video file")
    parser.add_argument("--interval", type=int, default=None, help="Extract every N seconds (overrides scene detection)")
    parser.add_argument("--out", default=None, help="Output folder (default: output/{name}-{timestamp})")
    parser.add_argument("--no-transcript", action="store_true", help="Skip audio transcription")
    args = parser.parse_args()

    video_path = os.path.abspath(args.video)
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        print("ffmpeg not found on PATH. Install it first.")
        sys.exit(1)

    name = Path(video_path).stem
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out) if args.out else Path(__file__).parent / "output" / f"{name}-{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / "frames"

    duration = probe_duration(video_path)
    print(f"Video: {video_path}")
    print(f"Duration: {duration:.0f}s")
    print(f"Output: {out_dir}")

    print("\nExtracting frames...")
    if args.interval:
        frames = extract_frames_interval(video_path, frames_dir, args.interval)
        mode = f"interval-{args.interval}s"
    else:
        frames = extract_frames_scene(video_path, frames_dir)
        mode = "scene-change"
        if not frames:
            print("  No scene-change frames detected. Falling back to 5s interval.")
            frames = extract_frames_interval(video_path, frames_dir, 5)
            mode = "interval-5s-fallback"
    print(f"  Extracted {len(frames)} frames ({mode})")

    segments = []
    if not args.no_transcript:
        print("\nTranscribing audio...")
        segments = transcribe_local_whisper(video_path)
        if segments:
            write_transcript_md(segments, out_dir / "transcript.md")
            print(f"  Wrote transcript.md ({len(segments)} segments)")

    manifest = {
        "video": video_path,
        "duration_sec": duration,
        "generated_at": datetime.now().isoformat(),
        "frame_mode": mode,
        "frames": [{"file": f"frames/{fn}", "timestamp_sec": ts} for fn, ts in frames],
        "transcript_segments": len(segments),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nDone. Feed this folder to an AI agent:\n  {out_dir}")


if __name__ == "__main__":
    main()
