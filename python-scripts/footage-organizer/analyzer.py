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
- broll-inserts: Extreme close-ups of hands, objects, food, products, gear, or details. Camera is very close.
- broll-environment: Landscapes, architecture, cityscapes, nature, or interiors where no person is the primary focus.
- establishing-shots: Wide angle shots that establish a location or set the scene context. Usually exterior or overhead.
- location-shots: Footage of a specific recognizable place — NYC street, office interior, restaurant, rooftop, etc.
- action-shots: High-energy movement — sports, running, vehicles, fast camera movement, dynamic sequences.
- broll-office: Office interiors, desk setups, workspace environments, co-working spaces.
- screen-recordings: Monitor or phone screen footage, dashboards, software UI, app demos, slide decks.
- duo-shots: Two people clearly visible in the same frame together.
- reaction-shots: A person reacting, listening, watching, or in an over-the-shoulder framing.
- product-shots: Products, merchandise, equipment, or gear displayed for showcasing purposes.
- miscellaneous: Doesn't fit any category above, or contains mixed/unclear content.

Rules:
- Reply with ONLY the category name, nothing else.
- Do not add punctuation, explanation, or extra words.
- If the clip could fit two categories, pick the dominant one.
- Default to miscellaneous only if you genuinely cannot classify it."""


def classify_video(frames_b64: list[str], filename: str) -> str:
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
        print(f"         [warn] unexpected label '{raw}' — using 'miscellaneous'")
        return "miscellaneous"

    return raw
