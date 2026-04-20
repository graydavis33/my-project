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

_PROMPT = f"""You are classifying raw footage from a freelance videographer's SD card.
You have 4 frames extracted from a single video clip (at 20%, 40%, 60%, and 80% through the clip).

Your job: pick exactly ONE category from the list below. If two categories could equally apply, you MUST return `misc` — do not guess. The videographer reviews `misc` clips manually, so a wrong confident answer is worse than `misc`.

Categories (return one of these strings exactly):
{_CATEGORY_LIST}

Definitions — pick the category whose PRIMARY VISUAL QUESTION matches the clip:

PEOPLE — addressing camera (subject is engaging the lens):
- interview-solo: ONE person, framed and clearly speaking to camera, static or near-static framing. Talking-head.
- interview-duo: TWO people in frame, both engaged in on-camera conversation or being interviewed together.
- walk-and-talk: Subject is BOTH moving through space AND speaking to camera (handheld follow, vlog-style). Movement is the discriminator vs interview-solo.

PEOPLE — not addressing camera:
- candid-people: One or two people in natural activity, NOT speaking to camera. Working, walking, lifestyle.
- reaction-listening: A person is reacting, listening, or shown over-the-shoulder. They are NOT the active speaker in the frame.
- crowd-group: THREE or more people. Group dynamic, audience, meeting room, gathering.

DETAILS / OBJECTS (close-ups where an object is the subject):
- insert-hands: Hands are the PRIMARY subject — typing, holding, gesturing, working. Face may be absent or out of focus.
- insert-product: A product, piece of gear, or equipment is the static subject of the frame.
- insert-food-drink: Food, beverages, or dining is the subject.
- insert-detail: Extreme close-up of an object, texture, or material that is NOT hands, NOT a product, NOT food.

SCREENS:
- screens-and-text: A computer monitor, phone screen, dashboard, app UI, or prominent text/signage is the subject.

ENVIRONMENTS:
- establishing-exterior: Wide exterior shot that identifies a location — skyline, building, street view. No person is the focus.
- establishing-interior: Wide interior shot of a venue or room. No person is the focus.
- environment-detail: Architectural detail, texture, ambient interior — no person is the focus, not a wide establisher.

MOVEMENT:
- action-sport-fitness: Sports, working out, physical activity is the subject.
- transit-vehicles: Cars, subways, taxis, transportation, or traffic is the subject.

CATCH-ALL:
- misc: Use this when (a) you cannot confidently classify, or (b) two categories could equally apply, or (c) the clip is too dark/blurry/short to read.

Output rules:
- Reply with ONLY the category name. Nothing else. No punctuation. No explanation.
- Use only the exact strings from the category list above.
- When in doubt: `misc`. The videographer prefers manual review over a wrong confident answer."""


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
        print(f"         [warn] unexpected label '{raw}' — using 'misc'")
        return "misc"

    return raw
