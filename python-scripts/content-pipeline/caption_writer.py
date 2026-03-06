"""
caption_writer.py
Uses Claude to write platform-specific captions and hooks for each identified clip.
"""

import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a social media copywriter for a videographer/content creator.
Write captions that drive engagement and views on short-form platforms.

Rules:
- TikTok: conversational, lowercase ok, use line breaks for readability, 2-3 hashtags max
- Instagram Reels: slightly more polished, strong CTA, 5-8 hashtags
- YouTube Shorts: keyword-rich title, short description, focus on search
- Every caption must have a hook in the first line — no "hey guys" or "in this video"
- CTAs should feel natural, not forced"""


def write_captions(clip: dict, video_context: str = "") -> dict:
    """
    Write platform-specific captions for a clip.
    Returns a dict with tiktok, reels, and shorts captions.
    """
    context_str = f"Full video context: {video_context}\n" if video_context else ""

    prompt = f"""{context_str}Write captions for this short-form clip:

Clip title: {clip.get('title', '')}
Hook: {clip.get('hook', '')}
Platform: {clip.get('platform', 'TikTok/Reels/Shorts')}
Reason it works: {clip.get('reason', '')}

Write captions for all 3 platforms:

### TikTok Caption
(conversational, punchy, 2-3 hashtags)

### Instagram Reels Caption
(slightly polished, strong CTA, 5-8 hashtags)

### YouTube Shorts Title + Description
(keyword-rich title on first line, short description below)"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "clip_title": clip.get("title", ""),
        "captions_raw": response.content[0].text.strip(),
    }


def write_all_captions(clips: list, video_context: str = "") -> list:
    """Write captions for all clips in one batched call."""
    if not clips:
        return []

    context_str = f"Full video context: {video_context}\n\n" if video_context else ""

    clips_text = ""
    for i, clip in enumerate(clips, 1):
        clips_text += (
            f"CLIP {i}: {clip.get('title', '')}\n"
            f"Hook: {clip.get('hook', '')}\n"
            f"Reason: {clip.get('reason', '')}\n\n"
        )

    prompt = f"""{context_str}Write platform-specific captions for each of these {len(clips)} short-form clips.

{clips_text}

For each clip, write:
### CLIP [number]: [title]

**TikTok:** (conversational, 2-3 hashtags max)

**Instagram Reels:** (polished, strong CTA, 5-8 hashtags)

**YouTube Shorts:** Title: [keyword-rich title]
Description: [2-3 sentences]"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return [{"captions_all": response.content[0].text.strip()}]
