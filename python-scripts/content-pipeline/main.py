"""
main.py
Content Repurposing Pipeline

Takes a long-form video and outputs:
  - 3-5 best short-form clip timestamps
  - Platform-specific captions + hooks for each clip
  - Optional: actual video cuts via ffmpeg

Usage:
  python main.py path/to/video.mp4
  python main.py path/to/video.mp4 --no-cut     (skip ffmpeg, output cut list only)
  python main.py path/to/video.mp4 --context "My video about AI editing tools"

Requirements:
  - ANTHROPIC_API_KEY in .env (always)
  - OPENAI_API_KEY in .env (optional — for auto-transcription via Whisper)
  - ffmpeg installed (optional — for auto video cutting)
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from transcriber import transcribe
from moment_picker import pick_moments, _fmt_time
from caption_writer import write_all_captions
from video_cutter import cut_all_clips
from config import OUTPUT_DIR

# ─── Logging ────────────────────────────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.dirname(__file__), "pipeline.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def _parse_args():
    args = sys.argv[1:]
    video_path = None
    skip_cut = "--no-cut" in args
    context = ""

    if "--context" in args:
        idx = args.index("--context")
        if idx + 1 < len(args):
            context = args[idx + 1]

    # First non-flag arg is video path
    for a in args:
        if not a.startswith("--"):
            video_path = a
            break

    return video_path, skip_cut, context


def save_results(base_name: str, clips: list, captions: list, cut_paths: list):
    """Save the cut list + captions to a text file in output/."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(OUTPUT_DIR, f"{base_name}-results-{timestamp}.txt")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"Content Repurposing Results — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Source: {base_name}\n")
        f.write("=" * 60 + "\n\n")

        f.write("CUT LIST\n")
        f.write("-" * 40 + "\n")
        for i, clip in enumerate(clips):
            start = clip.get("start_time")
            end = clip.get("end_time")
            time_str = f"{_fmt_time(start)} – {_fmt_time(end)}" if start and end else "timestamps unavailable"
            cut_str = f" → {cut_paths[i]}" if i < len(cut_paths) and cut_paths[i] else ""
            f.write(f"Clip {clip.get('clip_number', i+1)}: {clip.get('title', '')}\n")
            f.write(f"  Time: {time_str}{cut_str}\n")
            f.write(f"  Hook: {clip.get('hook', '')}\n")
            f.write(f"  Why: {clip.get('reason', '')}\n\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("CAPTIONS\n")
        f.write("-" * 40 + "\n\n")
        for c in captions:
            f.write(c.get("captions_all", "") + "\n\n")

    return out_file


def run_pipeline(video_path: str, skip_cut: bool = False, context: str = ""):
    base_name = Path(video_path).stem

    print(f"\n{'=' * 60}")
    print(f"  Content Pipeline: {base_name}")
    print(f"{'=' * 60}\n")

    # Step 1: Transcribe
    log.info("Step 1: Transcribing...")
    segments = transcribe(video_path)
    log.info(f"  {len(segments)} segment(s) transcribed")

    # Step 2: Pick moments
    log.info("Step 2: Identifying best moments with Claude...")
    clips = pick_moments(segments, context)
    if not clips:
        log.error("No clips identified — aborting")
        print("  ❌ Claude couldn't identify clips. Try providing --context.")
        return
    log.info(f"  {len(clips)} clip(s) identified")

    print(f"\n  Found {len(clips)} clip(s):\n")
    for clip in clips:
        start = clip.get("start_time")
        end = clip.get("end_time")
        time_str = f"{_fmt_time(start)} – {_fmt_time(end)}" if start and end else "no timestamps"
        print(f"  [{clip.get('clip_number', '?')}] {clip.get('title', '')} ({time_str})")
        print(f"       Hook: {clip.get('hook', '')}")
        print(f"       Why: {clip.get('reason', '')}\n")

    # Step 3: Write captions (batched, one Claude call)
    log.info("Step 3: Writing captions with Claude...")
    captions = write_all_captions(clips, context)
    log.info("  Captions written")

    # Step 4: Cut video (optional)
    cut_paths = []
    if not skip_cut:
        log.info("Step 4: Cutting clips with ffmpeg...")
        cut_paths = cut_all_clips(video_path, clips, base_name)
    else:
        cut_paths = [None] * len(clips)

    # Step 5: Save results
    out_file = save_results(base_name, clips, captions, cut_paths)
    print(f"\n  ✅ Results saved: {out_file}")
    log.info(f"Pipeline complete. Results: {out_file}")


if __name__ == "__main__":
    video_path, skip_cut, context = _parse_args()

    if not video_path:
        print(__doc__)
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"  ❌ File not found: {video_path}")
        sys.exit(1)

    try:
        run_pipeline(video_path, skip_cut, context)
    except Exception:
        log.exception("Pipeline failed")
