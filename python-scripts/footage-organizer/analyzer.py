"""
analyzer.py
Sends 4 video frames to Claude Haiku Vision and returns a category label.
"""
import os
import sys

import anthropic

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import track_response

from config import ANTHROPIC_API_KEY, MODEL, CATEGORIES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_CATEGORY_LIST = "\n".join(f"- {c}" for c in CATEGORIES)

_PROMPT = f"""You are analyzing footage from a freelance videographer's SD card.
You have been given 4 frames extracted from a single video clip (at 20%, 40%, 60%, and 80% through the video).

Classify this clip into exactly one of the following categories:
{_CATEGORY_LIST}

Category definitions:
- interviews: A person is speaking directly to or facing the camera. Talking-head style. The subject is clearly the focus.
- broll-people: People visible but NOT in interview position. Candid activity, walking, working, crowd shots, lifestyle.
- broll-environment: Landscapes, architecture, cityscapes, establishing shots, nature, interiors without people as the focus.
- inserts: Extreme close-ups of objects, hands, food, products, gear, or details. Camera is very close to the subject.
- action: High-energy movement — sports, running, vehicles, dynamic camera movement, fast-paced sequences.
- graphics-screens: Monitor footage, screen recordings, slideshows, text overlays, UI demonstrations.
- uncategorized: The frames are too dark, blurry, or ambiguous to classify confidently.

Rules:
- Reply with ONLY the category name, nothing else.
- Do not add punctuation, explanation, or extra words.
- If the clip could fit two categories, pick the dominant one.
- Default to uncategorized only if you genuinely cannot tell."""


def classify_video(frames_b64: list[str], filename: str) -> str:
    """
    Send 4 base64 JPEG frames to Claude Haiku Vision.
    Returns one category string from CATEGORIES.
    Falls back to 'uncategorized' if Claude returns an unexpected response.
    """
    content = []
    for b64 in frames_b64:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": b64,
            }
        })
    content.append({"type": "text", "text": _PROMPT})

    response = client.messages.create(
        model=MODEL,
        max_tokens=50,
        messages=[{"role": "user", "content": content}]
    )
    track_response(response)

    raw = response.content[0].text.strip().lower()

    if raw not in CATEGORIES:
        print(f"         [warn] unexpected label '{raw}' — using 'uncategorized'")
        return "uncategorized"

    return raw
