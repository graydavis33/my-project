"""
Hook + Title Optimizer
Generates platform-optimized titles, opening hooks, and thumbnail concepts for any video idea.

Usage:
  python main.py "your video concept"
  python main.py              (will prompt for input)
"""
import os
import sys
from dotenv import load_dotenv
import anthropic

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set in .env")
    sys.exit(1)

client = anthropic.Anthropic(api_key=api_key)

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


def optimize(concept: str) -> str:
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
    return message.content[0].text


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
    result = optimize(concept)
    print(result)
    print("=" * 55)


if __name__ == '__main__':
    main()
