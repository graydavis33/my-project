"""
transcriber.py
Transcribes a video file using OpenAI Whisper API.
Falls back to prompting for manual transcript if OPENAI_API_KEY is not set.

Returns a list of segments: [{"start": 0.0, "end": 5.2, "text": "..."}]
"""

import os
import sys
from config import OPENAI_API_KEY


def transcribe(video_path: str) -> list:
    """
    Transcribe the video and return timestamped segments.
    Tries local Whisper first (free, no size limit), then OpenAI Whisper API,
    then falls back to manual paste.
    """
    try:
        return _transcribe_with_local_whisper(video_path)
    except ImportError:
        if OPENAI_API_KEY:
            print("  Local Whisper not installed — falling back to OpenAI Whisper API.")
            return _transcribe_with_whisper(video_path)
        print("\n  ⚠️  No transcription backend available — switching to manual mode.")
        return _prompt_manual_transcript()


def _transcribe_with_local_whisper(video_path: str, model_name: str = "base") -> list:
    """
    Transcribe using the local openai-whisper package. Free, runs offline, no file size limit.
    Model sizes: tiny (39M), base (74M, default), small (244M), medium (769M), large (1550M).
    First run downloads the model (~140MB for 'base').
    """
    import whisper

    print(f"  Transcribing with local Whisper ({model_name} model)...")
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"  File size: {file_size_mb:.1f} MB")

    model = whisper.load_model(model_name)
    result = model.transcribe(video_path, verbose=False)

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 1),
            "end": round(seg["end"], 1),
            "text": seg["text"].strip(),
        })

    duration = segments[-1]["end"] if segments else 0
    print(f"  Transcribed {len(segments)} segment(s) ({duration:.0f}s total)")
    return segments


def _transcribe_with_whisper(video_path: str) -> list:
    """Transcribe using OpenAI Whisper API."""
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        print("  ⚠️  openai package not installed. Run: pip install openai")
        return _prompt_manual_transcript()

    print(f"  Transcribing with Whisper API...")
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"  File size: {file_size_mb:.1f} MB")

    if file_size_mb > 25:
        print("  ⚠️  File > 25MB — Whisper API limit. Consider compressing first.")
        print("  Tip: ffmpeg -i input.mp4 -vn -ar 16000 -ac 1 audio.mp3")
        print("  Then re-run with the audio file instead.")

    with open(video_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    segments = []
    for seg in response.segments:
        segments.append({
            "start": round(seg.start, 1),
            "end": round(seg.end, 1),
            "text": seg.text.strip(),
        })

    print(f"  Transcribed {len(segments)} segment(s) ({response.duration:.0f}s total)")
    return segments


def _prompt_manual_transcript() -> list:
    """
    Ask the user to paste a transcript manually.
    Returns a single segment (no timestamps — clip picker will estimate).
    """
    print("\n  Manual transcript mode.")
    print("  Paste your full transcript below. Press Enter twice when done.\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    transcript = "\n".join(lines[:-1]).strip()
    if not transcript:
        print("  No transcript provided. Exiting.")
        sys.exit(1)
    # Return as single block — moment_picker will work with text only
    return [{"start": 0, "end": 0, "text": transcript}]
