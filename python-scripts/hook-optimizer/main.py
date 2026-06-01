"""
Hook + Title Optimizer
Generates platform-optimized titles, opening hooks, and thumbnail concepts for any video idea.

Usage:
  python main.py "your video concept"
  python main.py              (will prompt for input)

Results are cached for 7 days and auto-saved to results/ folder.
"""
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set in .env")
    sys.exit(1)

client = anthropic.Anthropic(api_key=api_key)

_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
_CACHE_FILE = os.path.join(_RESULTS_DIR, "cache.json")
_CACHE_TTL = 7 * 24 * 3600  # 7 days

SYSTEM = """You are an expert social media strategist specializing in video content for creators \
in the videography, filmmaking, and AI/tech space. You know exactly what makes content go viral \
on YouTube, TikTok, and Instagram Reels.

Rules:
- Titles must be SPECIFIC, not generic. "I tried AI video editing for 30 days" beats "AI Editing Tips"
- YouTube titles: 60 chars max, lead with keywords, create a curiosity gap
- TikTok/Reels titles: conversational, punchy, can use lowercase for authenticity
- Hooks MUST work in the first 2 seconds — no slow intros, no "hey guys welcome back"
- Thumbnail text: 3 words or fewer, high contrast, readable at small size
- Your "Best Bet" pick should be the one YOU would bet money on"""


def _slug(concept: str) -> str:
    """Convert concept to a safe filename slug."""
    slug = re.sub(r'[^a-z0-9]+', '-', concept.lower().strip())
    return slug[:50].strip('-')


def _concept_hash(concept: str) -> str:
    return hashlib.md5(concept.strip().lower().encode()).hexdigest()


def _load_cache() -> dict:
    os.makedirs(_RESULTS_DIR, exist_ok=True)
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache: dict):
    os.makedirs(_RESULTS_DIR, exist_ok=True)
    with open(_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def _get_cached(concept: str):
    """Return cached result if it exists and is <7 days old, else None."""
    cache = _load_cache()
    key = _concept_hash(concept)
    entry = cache.get(key)
    if entry and time.time() - entry.get("cached_at", 0) < _CACHE_TTL:
        return entry["result"]
    return None


def _store_cached(concept: str, result: str):
    cache = _load_cache()
    cache[_concept_hash(concept)] = {
        "concept": concept,
        "result": result,
        "cached_at": time.time(),
    }
    _save_cache(cache)


def _save_result(concept: str, result: str, from_cache: bool):
    """Save result to results/{slug}-{timestamp}.txt"""
    os.makedirs(_RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{_slug(concept)}-{timestamp}.txt"
    filepath = os.path.join(_RESULTS_DIR, filename)
    header = f"Concept: {concept}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if from_cache:
        header += " (from cache)"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + "\n" + "=" * 55 + "\n\n" + result)
    return filepath


def optimize(concept: str) -> tuple[str, bool]:
    """
    Return (result_text, from_cache).
    Checks cache first; calls Claude if cache miss.
    """
    cached = _get_cached(concept)
    if cached:
        return cached, True

    prompt = f"""Video concept: {concept}

## YOUTUBE TITLES (5 options)
Optimized for search + clicks. Lead with keywords. Max 60 chars each.

## TIKTOK / REELS TITLES (5 options)
Conversational, punchy, trend-aware. Different angle from YouTube.

## OPENING HOOKS (3 options)
Script for the FIRST 3 SECONDS only. Three different angles:
- Option A: Bold statement or hot take
- Option B: Question that opens a curiosity gap
- Option C: Pattern interrupt or unexpected opener

## THUMBNAIL CONCEPT
One strong visual idea + text overlay (3 words max). Describe what's in the frame.

## BEST BET
Which title + hook combination would you lead with and why? (2 sentences max)"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    result = message.content[0].text
    _store_cached(concept, result)
    return result, False


def main():
    if len(sys.argv) > 1:
        concept = ' '.join(sys.argv[1:])
    else:
        print("=" * 55)
        print("    Hook + Title Optimizer")
        print("=" * 55)
        concept = input("\nVideo concept: ").strip()
        if not concept:
            print("No concept provided. Exiting.")
            sys.exit(1)

    print(f"\nOptimizing: \"{concept}\"\n")
    print("=" * 55)

    result, from_cache = optimize(concept)

    if from_cache:
        print("(cached result)\n")
    print(result)
    print("=" * 55)

    saved_path = _save_result(concept, result, from_cache)
    print(f"\nSaved to: {saved_path}")


if __name__ == '__main__':
    main()
