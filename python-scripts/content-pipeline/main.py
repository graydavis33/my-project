"""
main.py
Content Repurposing Pipeline

Takes a long-form video and outputs:
  - 3-5 best short-form clip timestamps
  - Platform-specific captions + hooks for each clip
  - Optional: actual video cuts via ffmpeg

Usage:
  python main.py path/to/video.mp4
  python main.py path/to/video.mp4 --no-cut             (skip ffmpeg, output cut list only)
  python main.py path/to/video.mp4 --context "..."      (give Claude context)
  python main.py path/to/video.mp4 --transcribe-only    (just dump a clean .md transcript)
  python main.py path/to/recording.m4a --meeting-notes  (transcribe + extract structured notes → Obsidian)

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
import anthropic
from config import OUTPUT_DIR, ANTHROPIC_API_KEY, OBSIDIAN_SAI_CONVERSATIONS

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
    transcribe_only = "--transcribe-only" in args
    meeting_notes = "--meeting-notes" in args
    context = ""

    if "--context" in args:
        idx = args.index("--context")
        if idx + 1 < len(args):
            context = args[idx + 1]

    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a == "--context":
            skip_next = True
            continue
        if not a.startswith("--"):
            video_path = a
            break

    return video_path, skip_cut, context, transcribe_only, meeting_notes


def save_transcript(video_path: str, segments: list) -> str:
    """Save a clean Markdown transcript of the video to output/."""
    base_name = Path(video_path).stem
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_file = os.path.join(OUTPUT_DIR, f"{base_name}-transcript-{timestamp}.md")

    duration = segments[-1]["end"] if segments and segments[-1].get("end") else 0

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"# Transcript: {base_name}\n\n")
        f.write(f"*Transcribed: {datetime.now().strftime('%Y-%m-%d %H:%M')}*  \n")
        if duration:
            mins, secs = divmod(int(duration), 60)
            f.write(f"*Duration: {mins}m {secs}s*  \n")
        f.write(f"*Segments: {len(segments)}*\n\n")
        f.write("---\n\n")

        # Full prose — paragraph break every ~6 segments for readability
        para = []
        for i, seg in enumerate(segments, 1):
            para.append(seg["text"])
            if i % 6 == 0:
                f.write(" ".join(para) + "\n\n")
                para = []
        if para:
            f.write(" ".join(para) + "\n\n")

    return out_file


def save_meeting_notes(audio_path: str, segments: list) -> str:
    """Transcribe a voice memo, extract structured notes with Haiku, save to Obsidian."""
    full_transcript = " ".join(seg["text"] for seg in segments)
    date_str = datetime.now().strftime("%Y-%m-%d")
    base_name = Path(audio_path).stem

    print("  Extracting structured notes with Claude Haiku...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                "You are extracting notes from a voice conversation between Gray Davis "
                "(Creative Director) and Sai Karra (his client / employer). "
                "Read the transcript and return ONLY the following markdown sections — "
                "no intro, no commentary:\n\n"
                "## Summary\n"
                "2-3 sentences covering what was discussed.\n\n"
                "## Content Ideas\n"
                "Bullet list of any content ideas, formats, or concepts mentioned.\n\n"
                "## Decisions & Priorities\n"
                "Bullet list of any decisions made or priorities set.\n\n"
                "## Action Items\n"
                "Checkbox list of specific next steps for Gray or Sai.\n\n"
                f"Transcript:\n{full_transcript}"
            )
        }]
    )
    structured = response.content[0].text.strip()

    vault_parent = os.path.dirname(OBSIDIAN_SAI_CONVERSATIONS)
    if not os.path.isdir(vault_parent):
        raise FileNotFoundError(
            f"Obsidian vault parent not found: {vault_parent}\n"
            f"  Is Google Drive for Desktop running and synced?\n"
            f"  Set OBSIDIAN_SAI_CONVERSATIONS in .env to the correct path for this machine."
        )
    os.makedirs(OBSIDIAN_SAI_CONVERSATIONS, exist_ok=True)
    out_file = os.path.join(OBSIDIAN_SAI_CONVERSATIONS, f"{date_str}-{base_name}.md")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"# {date_str} — {base_name}\n\n")
        f.write(structured)
        f.write("\n\n---\n\n## Full Transcript\n\n")
        for seg in segments:
            f.write(seg["text"].strip() + " ")

    os.remove(audio_path)
    print(f"  [OK] Audio deleted: {audio_path}")

    return out_file


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


def run_pipeline(video_path: str, skip_cut: bool = False, context: str = "", transcribe_only: bool = False, meeting_notes: bool = False):
    base_name = Path(video_path).stem

    print(f"\n{'=' * 60}")
    print(f"  Content Pipeline: {base_name}")
    print(f"{'=' * 60}\n")

    # Step 1: Transcribe
    log.info("Step 1: Transcribing...")
    segments = transcribe(video_path)
    log.info(f"  {len(segments)} segment(s) transcribed")

    if meeting_notes:
        out_file = save_meeting_notes(video_path, segments)
        print(f"\n  [OK] Meeting notes saved: {out_file}")
        log.info(f"Meeting notes complete. File: {out_file}")
        return

    if transcribe_only:
        out_file = save_transcript(video_path, segments)
        print(f"\n  [OK] Transcript saved: {out_file}")
        log.info(f"Transcribe-only complete. Transcript: {out_file}")
        return

    # Step 2: Pick moments
    log.info("Step 2: Identifying best moments with Claude...")
    clips = pick_moments(segments, context)
    if not clips:
        log.error("No clips identified — aborting")
        print("  [X] Claude couldn't identify clips. Try providing --context.")
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
    print(f"\n  [OK] Results saved: {out_file}")
    log.info(f"Pipeline complete. Results: {out_file}")


if __name__ == "__main__":
    video_path, skip_cut, context, transcribe_only, meeting_notes = _parse_args()

    if not video_path:
        print(__doc__)
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"  [X] File not found: {video_path}")
        sys.exit(1)

    try:
        run_pipeline(video_path, skip_cut, context, transcribe_only, meeting_notes)
    except Exception:
        log.exception("Pipeline failed")
