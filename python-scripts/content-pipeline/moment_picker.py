"""
moment_picker.py
Uses Claude to identify the best short-form moments from a long-form video transcript.
Returns a list of clip suggestions with timestamps, titles, and reasoning.
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, MAX_CLIPS, CLIP_MIN_SECONDS, CLIP_MAX_SECONDS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a short-form content strategist specializing in repurposing long-form videos
into viral TikTok, Instagram Reels, and YouTube Shorts for videographers and content creators.

You know that the best short clips:
- Have a clear, standalone hook within the first 3 seconds
- Deliver one specific insight, story, or moment (not a vague overview)
- Work without context from the full video
- Have natural start/end points (don't cut mid-sentence)"""


def pick_moments(segments: list, video_context: str = "") -> list:
    """
    Identify the best short-form moments from transcript segments.
    Returns a list of clip dicts with: start, end, title, hook, reason
    """
    has_timestamps = any(s.get("end", 0) > 0 for s in segments)

    # Build transcript text for Claude
    if has_timestamps:
        transcript_text = "\n".join(
            f"[{_fmt_time(s['start'])} – {_fmt_time(s['end'])}] {s['text']}"
            for s in segments
        )
    else:
        # Manual transcript — no timestamps
        transcript_text = segments[0]["text"] if segments else ""

    context_str = f"\nVideo context: {video_context}\n" if video_context else ""

    timestamp_instructions = (
        "Include 'start_time' and 'end_time' as seconds (e.g. 145.0) from the timestamps shown."
        if has_timestamps
        else "Since there are no timestamps, set start_time and end_time to null."
    )

    prompt = f"""Here is the transcript of a long-form video.{context_str}

Identify the {MAX_CLIPS} best moments to clip for short-form content (TikTok/Reels/Shorts).
Each clip should be {CLIP_MIN_SECONDS}–{CLIP_MAX_SECONDS} seconds long.

TRANSCRIPT:
{transcript_text[:8000]}

{timestamp_instructions}

Return ONLY a JSON array of {MAX_CLIPS} clip objects in this exact format:
[
  {{
    "clip_number": 1,
    "title": "Short-form title (max 60 chars)",
    "start_time": 145.0,
    "end_time": 205.0,
    "hook": "Opening line/action for the first 3 seconds",
    "platform": "TikTok/Reels/Shorts",
    "reason": "Why this moment works as a short (1 sentence)"
  }}
]"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    try:
        clips = json.loads(text)
        return clips if isinstance(clips, list) else []
    except json.JSONDecodeError:
        # Try to extract JSON array from response
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        return []


def _fmt_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"
