"""
Photo Organizer — Visual Location Grouper
Uses Claude Haiku to look at each photo and identify the scene/location
from the visuals — no GPS required.

Flow:
  1. Send each photo thumbnail to Haiku → get a short location description
  2. Collect all unique descriptions
  3. Send descriptions to Haiku once → get back clean, grouped folder names
  4. Return {folder_name: [filepath, ...]}

Results are cached to disk so re-runs are instant and cost nothing extra.
"""

import json
import os
import time
from typing import Optional

import anthropic

from config import (
    VISION_CACHE_FILE,
    VISION_MODEL,
    VISION_THUMBNAIL_PX,
    VISION_GROUP_BATCH,
)
from extractor import make_thumbnail_b64


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _load_cache(cache_path: str) -> dict:
    if os.path.exists(cache_path):
        try:
            with open(cache_path) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict, cache_path: str):
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


# ── Step 1: Describe each photo's location ────────────────────────────────────

def describe_location(
    filepath: str,
    client: anthropic.Anthropic,
    cache: dict,
    cache_path: str,
) -> str:
    """
    Ask Claude Haiku: what location/scene is in this photo?
    Returns a short description string. Uses cache to avoid repeat calls.
    """
    if filepath in cache:
        return cache[filepath]

    b64 = make_thumbnail_b64(filepath, VISION_THUMBNAIL_PX)
    if b64 is None:
        desc = "unreadable"
        cache[filepath] = desc
        _save_cache(cache, cache_path)
        return desc

    try:
        response = client.messages.create(
            model=VISION_MODEL,
            max_tokens=30,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "What location or setting is shown in this photo? "
                            "Answer in 3–5 words only. Be specific and consistent. "
                            "Examples: 'rocky mountain trail', 'tropical beach', "
                            "'urban city street', 'forest waterfall', 'desert canyon'. "
                            "Just the location phrase, nothing else."
                        ),
                    },
                ],
            }],
        )
        desc = response.content[0].text.strip().lower()
    except Exception as e:
        desc = "unknown location"

    cache[filepath] = desc
    _save_cache(cache, cache_path)
    return desc


# ── Step 2: Consolidate descriptions into clean folder names ──────────────────

def consolidate_descriptions(
    descriptions: list,
    client: anthropic.Anthropic,
) -> dict:
    """
    Takes a list of raw location descriptions (may have duplicates/variants)
    and uses Claude to group similar ones into clean folder names.

    Returns: {raw_description: "Clean Folder Name"}
    """
    unique = list(set(descriptions))
    if not unique:
        return {}

    # Process in batches (Haiku has a context limit)
    mapping = {}
    for i in range(0, len(unique), VISION_GROUP_BATCH):
        batch = unique[i : i + VISION_GROUP_BATCH]
        batch_str = "\n".join(f"- {d}" for d in batch)

        prompt = (
            "Below is a list of location descriptions taken from photos. "
            "Group similar descriptions together and assign each group a clean, "
            "short folder name (2–4 title-case words). "
            "Return ONLY valid JSON in this format:\n"
            '{"raw description": "Clean Folder Name", ...}\n\n'
            "Descriptions:\n"
            f"{batch_str}\n\n"
            "Rules:\n"
            "- Merge clearly similar descriptions (e.g. 'sandy beach' + 'tropical beach' → 'Beach')\n"
            "- Keep genuinely different locations separate\n"
            "- Folder names should be 2–4 words, title-case, no special characters\n"
            "- Return ONLY the JSON object, nothing else"
        )

        try:
            response = client.messages.create(
                model=VISION_MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            batch_map = json.loads(text)
            mapping.update(batch_map)
        except Exception:
            # If parsing fails, use the raw description as the folder name
            for d in batch:
                mapping[d] = d.title()

    return mapping


# ── Main entry point ──────────────────────────────────────────────────────────

def build_location_groups(
    photo_paths: list,
    cache_path: str,
    api_key: str,
    progress_callback=None,
) -> dict:
    """
    Analyze all photos visually and group them by location.
    Returns {location_folder_name: [filepath, ...]}

    photo_paths: list of file paths to analyze
    cache_path:  where to store the vision cache JSON
    api_key:     Anthropic API key
    """
    client = anthropic.Anthropic(api_key=api_key)
    cache = _load_cache(cache_path)

    # Step 1 — describe each photo
    descriptions = {}   # filepath → raw description string
    total = len(photo_paths)

    for i, path in enumerate(photo_paths):
        desc = describe_location(path, client, cache, cache_path)
        descriptions[path] = desc
        if progress_callback:
            progress_callback(i + 1, total, f"{desc}  ←  {os.path.basename(path)}")

    # Step 2 — consolidate into clean folder names
    raw_descs = list(descriptions.values())
    desc_to_folder = consolidate_descriptions(raw_descs, client)

    # Step 3 — group filepaths by folder name
    groups: dict = {}
    for path, raw_desc in descriptions.items():
        folder = desc_to_folder.get(raw_desc, raw_desc.title())
        # Sanitize folder name (remove characters Windows/Mac can't handle)
        for ch in r'/\:*?"<>|':
            folder = folder.replace(ch, "-")
        folder = folder.strip()
        groups.setdefault(folder, []).append(path)

    return groups
