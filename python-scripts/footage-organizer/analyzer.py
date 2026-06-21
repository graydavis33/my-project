"""
analyzer.py
Sends 4 video frames to Claude Haiku Vision and returns a category label.
"""
import os
import sys

import anthropic

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import track_response

import json

from config import ANTHROPIC_API_KEY, MODEL, CATEGORIES, EMOTION_TAGS, ACTION_TAGS

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


# ── v4 b-roll Vision tagging ────────────────────────────────────────────────

_TAG_PROMPT = f"""You are tagging one reusable B-ROLL clip from a videographer's library.
You have 4 frames sampled across the clip (20%, 40%, 60%, 80%).

Return a single JSON object describing the clip for later search. Keys:
- "person_present" (boolean): true if a PERSON is a clear subject of the clip.
- "emotion" (string or null): the person's mood — ONLY when person_present is true, else null.
    Prefer one of: {", ".join(EMOTION_TAGS)} (a different single word is OK if none fit).
- "action" (string or null): what the person is doing — ONLY when person_present is true, else null.
    Prefer one of: {", ".join(ACTION_TAGS)} (a different short word is OK if none fit).
- "location" (string): the setting/place, lowercase, 1-3 words (e.g. "nyc street", "office",
    "bedroom", "cafe", "gym", "subway"). Always give your best read.
- "objects" (array of strings): notable objects in frame, lowercase short nouns
    (e.g. "coffee cup", "laptop", "car", "building"). Most important for clips with NO person.
    Use [] if nothing notable.

Rules:
- Output ONLY the JSON object. No markdown fences, no prose, no trailing text.
- emotion and action MUST be null when person_present is false.
- Keep every tag lowercase. Be concise and consistent so tags group well across clips."""


def _coerce_tags(data: dict) -> dict:
    """Normalize the model's JSON into the canonical tag shape with safe types.
    Enforces the rule that emotion/action exist only when a person is present."""
    person = bool(data.get("person_present"))
    def _norm(v):
        return v.strip().lower() if isinstance(v, str) and v.strip() else None
    objs = data.get("objects") or []
    if not isinstance(objs, list):
        objs = []
    objs = [o.strip().lower() for o in objs if isinstance(o, str) and o.strip()]
    return {
        "person_present": person,
        "emotion": _norm(data.get("emotion")) if person else None,
        "action": _norm(data.get("action")) if person else None,
        "location": _norm(data.get("location")),
        "objects": objs,
    }


def tag_video(frames_b64: list[str], filename: str, model: str) -> dict:
    """Vision-tag one clip → {person_present, emotion, action, location, objects}.
    Uses a strict JSON-only prompt (SDK-version-robust — no output_config needed)."""
    content = [{
        "type": "image",
        "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
    } for b64 in frames_b64]
    content.append({"type": "text", "text": _TAG_PROMPT})

    response = client.messages.create(
        model=model,
        max_tokens=400,
        messages=[{"role": "user", "content": content}],
    )
    track_response(response)

    raw = next((b.text for b in response.content if b.type == "text"), "").strip()
    # Strip accidental markdown fences before parsing.
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{"):raw.rfind("}") + 1]
    return _coerce_tags(json.loads(raw))
