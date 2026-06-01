"""
Uses Claude Sonnet to pick the 3 best AI news stories and write a fully scripted Short.
Haiku handles story scoring; Sonnet handles the creative script writing.
Results are cached by story hash — if same stories + same feedback, skip the API call.
"""

import json
import hashlib
import anthropic
from config import (
    ANTHROPIC_API_KEY, CHANNEL_NAME, NUM_STORIES,
    HOOK_WORDS, STORY_WORDS, OUTRO_WORDS, TMP_DIR,
)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_CACHE_FILE = TMP_DIR / 'script_cache.json'

# ─── System prompt ────────────────────────────────────────────────────────────
_SYSTEM = f"""You are the lead scriptwriter for {CHANNEL_NAME}, a YouTube Shorts channel covering AI news.

Your audience: tech-savvy people aged 18-35 who want to stay ahead on AI. They scroll fast — you have 2 seconds to hook them.

Tone: POLARIZING, ENTERTAINING, SPECIFIC. Like a tech-savvy friend who can't believe what they're reading. Never corporate. Never hedged. Never "AI could potentially" — be decisive.

STRICT word counts (for timing — do not exceed):
- Hook: {HOOK_WORDS} words max (5 seconds on camera)
- Each story narration: {STORY_WORDS} words max (12 seconds of B-roll)
- Outro: {OUTRO_WORDS} words max (4 seconds on camera)

Hook rules:
- Start with a shocking fact, number, or reversal — never "Welcome back" or "Hey guys"
- Example: "A $6 million Chinese AI just beat GPT-4. OpenAI spent 100x more. Here's what no one's talking about."

Story narration rules:
- Lead with the most surprising or uncomfortable fact
- Include one specific number, company name, or dollar amount
- End with why it matters or what's insane about it
- No padding, no "interestingly", no filler

Outro rules:
- Create urgency: "Tomorrow's story is even wilder" or "This is just the beginning"
- Always end with "Follow {CHANNEL_NAME}"

Return ONLY valid JSON, no markdown wrapper:
{{
  "hook": "...",
  "stories": [
    {{
      "title": "5-7 word punchy title",
      "narration": "Full narration text ({STORY_WORDS} words max)",
      "broll_keywords": ["keyword1", "keyword2", "keyword3"],
      "source_url": "https://..."
    }}
  ],
  "outro": "...",
  "youtube_title": "Engaging title for YouTube (under 70 chars, no clickbait promises you can't keep)",
  "description": "2-3 sentence YouTube description + relevant hashtags. Include #shorts #ai #ainews"
}}"""


# ─── Public API ───────────────────────────────────────────────────────────────

def write_script(stories: list[dict], feedback: str = None, revision: int = 0) -> dict:
    """
    Given raw news stories, return a structured script JSON.
    Caches by story+feedback hash — won't re-call API on identical inputs.
    """
    cache_key = _cache_key(stories, feedback)
    cached = _load_cache()
    if cache_key in cached and not feedback:
        print("[script] Cache hit — reusing previous script")
        return cached[cache_key]

    print(f"[script] Calling Claude Sonnet (revision {revision})...")
    script = _call_claude(stories, feedback)

    cached[cache_key] = script
    _CACHE_FILE.write_text(json.dumps(cached, indent=2))
    return script


def format_for_slack(script: dict) -> str:
    """Format script as a readable Slack message for Gray's review."""
    lines = [
        f"*Script ready for review — {script.get('youtube_title', 'AI News Short')}*",
        "",
        f"*HOOK (avatar, ~5 sec):*",
        f"> {script['hook']}",
        "",
    ]
    for i, story in enumerate(script['stories'], 1):
        lines += [
            f"*STORY {i}: {story['title']}*",
            f"> {story['narration']}",
            f"_Source: {story['source_url']}_",
            f"_B-roll keywords: {', '.join(story['broll_keywords'])}_",
            "",
        ]
    lines += [
        f"*OUTRO (avatar, ~4 sec):*",
        f"> {script['outro']}",
        "",
        f"*YouTube title:* {script['youtube_title']}",
        "",
        "Reply `approve` to continue, or type your feedback to revise.",
    ]
    return "\n".join(lines)


# ─── Internal ─────────────────────────────────────────────────────────────────

def _call_claude(stories: list[dict], feedback: str = None) -> dict:
    story_block = json.dumps(stories, indent=2)

    user_msg = f"Here are today's AI news stories:\n\n{story_block}"
    if feedback:
        user_msg += f"\n\n---\nFeedback on previous script: {feedback}\n\nPlease revise accordingly. Keep any stories not mentioned. Replace or reorder as directed."

    resp = _client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=1200,
        system=_SYSTEM,
        messages=[{'role': 'user', 'content': user_msg}],
    )

    raw = resp.content[0].text.strip()
    # Strip any accidental markdown fences
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.startswith('json'):
            raw = raw[4:]

    return json.loads(raw.strip())


def _cache_key(stories: list[dict], feedback: str = None) -> str:
    titles = '|'.join(s['title'] for s in stories[:10])
    payload = f"{titles}::{feedback or ''}"
    return hashlib.md5(payload.encode()).hexdigest()


def _load_cache() -> dict:
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text())
        except Exception:
            pass
    return {}
