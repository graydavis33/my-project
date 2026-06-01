"""
Claude Sonnet analysis: one batch call covering all 9 report sections.
Result is cached for 7 days by concept hash.
"""
import os
import sys
from dotenv import load_dotenv
import anthropic
from cache import get_cached, store_cached

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import track_response

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

_SECTIONS = """## PERFORMANCE DATA
Markdown table with columns: Rank | Title (truncated to 40 chars) | Views | Likes | Comments | Duration | Outlier Score | URL

## WHY EACH WAS AN OUTLIER
For each video, 2-3 sentences explaining what specific element drove outsized performance (hook, title angle, format, timing, topic, emotion, etc.)

## TOP 5 HOOK PATTERNS
The 5 most effective hook types found across these videos. For each: name the pattern, explain why it works, and give a verbatim example from the transcripts (or from the title if no transcript).

## FORMAT & LENGTH RECOMMENDATIONS
What video formats (listicle, tutorial, vlog, reaction, story, etc.) and lengths (in minutes) performed best. Be specific — cite examples.

## HIGH-VALUE KEYWORDS
Bulleted list of the most powerful words/phrases from top video titles and descriptions. Group them: topic keywords, emotional triggers, format indicators.

## 5 MINI HOOKS FOR GRAY'S CONCEPT
5 ready-to-use opening hooks specifically written for: "{concept}"
Each hook must work in the first 3 seconds. Label each with its hook type (bold statement, curiosity gap, pattern interrupt, statistic, story open).

## SCRIPT OUTLINE
A structural outline for Gray's video on: "{concept}"
Sections: Hook (3-10 sec) → Problem/Setup → Value Promise → Main Body (3-5 sub-sections) → CTA
For each section: name, purpose (1 sentence), suggested duration.

## FULL SCRIPT DRAFT
A complete word-for-word script draft written in Gray's voice — casual, direct, first-person. No "hey guys welcome back." Open with the hook. Target 3-5 minutes when spoken aloud (~450-750 words). Include natural pacing cues in [brackets] where helpful.

## PACING & SOUND DESIGN NOTES
Specific recommendations: cut timing (fast cuts vs. slow), music energy (high/low/none), b-roll moments, visual transitions, thumbnail angle — all inferred from what made these outliers work."""


def _build_prompt(concept: str, videos: list[dict]) -> str:
    lines = [
        f'Gray\'s video concept: "{concept}"\n',
        f"Top {len(videos)} outlier videos (ranked by views-to-subscriber ratio):\n",
        "---",
    ]

    for i, v in enumerate(videos, 1):
        hook = v.get('hook_transcript', '')
        hook_text = f"\nHook transcript (first 90s):\n{hook}" if hook else "\n(No transcript available)"
        lines.append(
            f"\nVIDEO {i}: {v['title']}\n"
            f"URL: {v['url']}\n"
            f"Channel: {v['channel_name']} | Subscribers: {v['subscribers']:,}\n"
            f"Published: {v['published_at']} | Duration: {v['duration']}\n"
            f"Views: {v['views']:,} | Likes: {v['likes']:,} | Comments: {v['comments']:,}\n"
            f"Outlier Score: {v['outlier_score']}x (views ÷ subscribers)"
            f"{hook_text}\n"
            "---"
        )

    sections = _SECTIONS.replace('"{concept}"', f'"{concept}"')
    lines.append(
        f"\nAnalyze these {len(videos)} outlier videos and produce a research report for Gray "
        f"in the following sections (use exact headers as shown):\n\n{sections}"
    )

    return '\n'.join(lines)


def analyze(concept: str, videos: list[dict]) -> str:
    """
    Run Claude Sonnet analysis on outlier videos. Cached 7 days.
    Returns full markdown report string.
    """
    cached = get_cached(concept)
    if cached:
        return cached

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY not set in .env"

    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(concept, videos)

    print(f"  [analyzer] Sending {len(videos)} videos to Claude Sonnet...")
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=(
            "You are an expert video content strategist who specializes in analyzing what makes "
            "YouTube videos go viral. You study outlier videos — those that massively overperformed "
            "relative to their channel size — and extract actionable patterns for creators. "
            "Be specific, cite real examples from the data, and write in a direct, no-fluff style."
        ),
        messages=[{"role": "user", "content": prompt}]
    )
    track_response(msg)

    result = msg.content[0].text
    store_cached(concept, result)
    return result
