"""
analyzer.py
Uses Claude to analyze trending patterns across all monitored creators
and generate a weekly intelligence report.
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a social media intelligence analyst specializing in YouTube content strategy
for videographers and content creators. You identify patterns in what's working across top creators
so that Gray Davis can model proven strategies instead of guessing.

Be specific and actionable. Reference actual titles and creators when identifying patterns.
Avoid vague advice — give Gray concrete things he can do this week."""


def analyze_creator_data(videos: list) -> str:
    """
    Send all creator video data to Claude in one batch call.
    Returns a formatted intelligence report as a string.
    """
    # Build a concise summary of all videos for the prompt
    creator_summaries = {}
    for v in videos:
        c = v["creator"]
        if c not in creator_summaries:
            creator_summaries[c] = []
        creator_summaries[c].append({
            "title": v["title"],
            "views": v["views"],
            "published": v["published_at"],
        })

    # Format for prompt — top 5 videos per creator
    data_text = ""
    for creator, vids in creator_summaries.items():
        top = sorted(vids, key=lambda x: x["views"], reverse=True)[:5]
        data_text += f"\n{creator}:\n"
        for v in top:
            data_text += f"  - \"{v['title']}\" — {v['views']:,} views ({v['published']})\n"

    prompt = f"""Here is the latest YouTube data from {len(creator_summaries)} top creators in the videography/content space.
Analyze this data and write a weekly intelligence report for Gray Davis.

CREATOR DATA:
{data_text}

Write a report with these sections:

## 🔥 Top Trending Formats This Week
What types of videos are getting the most views right now? (3 specific format patterns)

## 🎣 Most Effective Hook Styles
What hooks/title structures are driving clicks? (with examples from actual titles above)

## 📅 Best Posting Patterns
What days/timing patterns do you see in the high-performing videos?

## 💡 Topics Gray Should Cover
3-5 specific video ideas Gray could make this week, based on what's clearly working right now.
For each: suggest a specific title and why it would work.

## ⚡ One Immediate Action
The single most important thing Gray should do differently based on this week's data. 1-2 sentences.

Keep the whole report under 400 words. Be specific, not generic."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
