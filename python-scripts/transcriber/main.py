"""
main.py
Transcriber — audio/video → text

Turns any audio or video into a clean transcript using local Whisper.
Two output modes:

  python main.py path/to/video.mp4                       dump a clean .md transcript to output/
  python main.py path/to/recording.m4a --meeting-notes   transcribe + extract structured notes -> Obsidian
  python main.py <folder> --meeting-notes --all          batch every .m4a in a folder

Requirements:
  - Local Whisper (pip install openai-whisper) — the default, free, offline transcription backend
  - ANTHROPIC_API_KEY in .env   (ONLY for --meeting-notes: Claude Haiku extracts the notes)
  - OPENAI_API_KEY in .env      (optional — Whisper API fallback if local Whisper isn't installed)
  - OBSIDIAN_VOICE_MEMOS in .env (required on Windows — where --meeting-notes saves)
"""

import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from transcriber import transcribe
import anthropic
from config import OUTPUT_DIR, ANTHROPIC_API_KEY, OBSIDIAN_VOICE_MEMOS

# ─── Logging ────────────────────────────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.dirname(__file__), "transcriber.log")
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
    meeting_notes = "--meeting-notes" in args
    batch = "--all" in args
    video_path = next((a for a in args if not a.startswith("--")), None)
    return video_path, meeting_notes, batch


def save_transcript(video_path: str, segments: list) -> str:
    """Save a clean Markdown transcript to output/."""
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


_DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\b[\s\-_]*(.*)$")


def _date_and_title_from_name(audio_path: str) -> tuple[str, str]:
    """Parse YYYY-MM-DD prefix from filename. Falls back to today's date."""
    stem = Path(audio_path).stem
    m = _DATE_PREFIX_RE.match(stem)
    if m:
        return m.group(1), (m.group(2).strip() or stem)
    return datetime.now().strftime("%Y-%m-%d"), stem


def save_meeting_notes(audio_path: str, segments: list) -> str:
    """Transcribe a voice memo, extract structured notes with Haiku, save to Obsidian."""
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "--meeting-notes needs ANTHROPIC_API_KEY in .env (Claude Haiku writes the notes).\n"
            "  Add it to python-scripts/transcriber/.env and re-run.\n"
            "  (A plain transcript without --meeting-notes needs no keys.)"
        )

    full_transcript = " ".join(seg["text"] for seg in segments)
    date_str, title = _date_and_title_from_name(audio_path)
    base_name = title

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

    vault_parent = os.path.dirname(OBSIDIAN_VOICE_MEMOS)
    if not os.path.isdir(vault_parent):
        raise FileNotFoundError(
            f"Obsidian vault parent not found: {vault_parent}\n"
            f"  Is Google Drive for Desktop running and synced?\n"
            f"  Set OBSIDIAN_VOICE_MEMOS in .env to the correct path for this machine."
        )
    os.makedirs(OBSIDIAN_VOICE_MEMOS, exist_ok=True)
    out_file = os.path.join(OBSIDIAN_VOICE_MEMOS, f"{date_str}-{base_name}.md")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"# {date_str} — {base_name}\n\n")
        f.write("← [[_Index|Voice Memos Index]]\n\n")
        f.write(structured)
        f.write("\n\n---\n\n## Full Transcript\n\n")
        for seg in segments:
            f.write(seg["text"].strip() + " ")

    os.remove(audio_path)
    print(f"  [OK] Audio deleted: {audio_path}")

    return out_file


def run(path: str, meeting_notes: bool = False):
    base_name = Path(path).stem

    print(f"\n{'=' * 60}")
    print(f"  Transcriber: {base_name}")
    print(f"{'=' * 60}\n")

    log.info("Transcribing...")
    segments = transcribe(path)
    log.info(f"  {len(segments)} segment(s) transcribed")

    if meeting_notes:
        out_file = save_meeting_notes(path, segments)
        print(f"\n  [OK] Meeting notes saved: {out_file}")
        log.info(f"Meeting notes complete. File: {out_file}")
    else:
        out_file = save_transcript(path, segments)
        print(f"\n  [OK] Transcript saved: {out_file}")
        log.info(f"Transcript complete: {out_file}")

    return out_file


if __name__ == "__main__":
    video_path, meeting_notes, batch = _parse_args()

    if batch:
        if video_path and os.path.isdir(video_path):
            input_dir = video_path
        else:
            input_dir = os.path.join(os.path.dirname(__file__), "input")
        audio_exts = {".m4a", ".mp3", ".wav", ".mp4", ".mov"}
        files = sorted(
            p for p in Path(input_dir).iterdir()
            if p.is_file() and p.suffix.lower() in audio_exts
        )
        if not files:
            print(f"  [X] No audio/video files found in {input_dir}")
            sys.exit(1)
        print(f"  Scanning: {input_dir}")
        print(f"  Found {len(files)} file(s) to process.\n")
        for f in files:
            try:
                run(str(f), meeting_notes)
            except Exception:
                log.exception(f"Failed: {f.name}")
        sys.exit(0)

    if not video_path:
        print(__doc__)
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"  [X] File not found: {video_path}")
        sys.exit(1)

    try:
        run(video_path, meeting_notes)
    except Exception:
        log.exception("Transcription failed")
