"""
AI Analyzer — generates insights from combined YouTube + TikTok stats.
Returns plain text. Caches in ai_insights table for 7 days per user.
"""
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()


def _safe_title(title):
    if not isinstance(title, str):
        return ''
    return title.replace('\n', ' ').replace('\r', ' ')[:120]


def _build_prompt(stats):
    """Build the Claude prompt from the combined stats dict."""
    all_videos = []
    platform_summaries = []

    yt = stats.get('youtube')
    if yt and yt.get('videos'):
        all_videos.extend(yt['videos'])
        platform_summaries.append(
            f"YouTube: {yt.get('channel_name', 'your channel')} — "
            f"{yt.get('subscriber_count', 0):,} subscribers, {len(yt['videos'])} videos"
        )

    tt = stats.get('tiktok')
    if tt and tt.get('videos'):
        all_videos.extend(tt['videos'])
        platform_summaries.append(
            f"TikTok: @{tt.get('username', '')} — "
            f"{tt.get('follower_count', 0):,} followers, {len(tt['videos'])} videos"
        )

    if not all_videos:
        return None

    total = len(all_videos)
    top = sorted(all_videos, key=lambda x: x.get('views', 0), reverse=True)[:8]
    avg_views = sum(v.get('views', 0) for v in all_videos) / total

    def fmt(v):
        eng = v.get('likes', 0) + v.get('comments', 0) + v.get('shares', 0)
        views = v.get('views', 0)
        eng_rate = f"{(eng / views * 100):.1f}%" if views > 0 else "—"
        return (
            f"  [{v.get('platform', '')}] \"{_safe_title(v.get('title', ''))}\"\n"
            f"  {v.get('views', 0):,} views · {v.get('likes', 0):,} likes · "
            f"{v.get('comments', 0):,} comments · {eng_rate} engagement\n"
        )

    platforms_str = ' | '.join(platform_summaries)

    return f"""You are a sharp, direct content strategy coach reviewing a creator's analytics. Your job is to give them a fast, honest read on their data.

CREATOR DATA:
{platforms_str}
Total videos: {total} | Avg views: {avg_views:,.0f}

TOP PERFORMING VIDEOS:
{''.join(fmt(v) for v in top)}

Write your analysis in exactly 4 short sections. Each section has a bold title on its own line, followed by 2–3 sentences of plain prose. No bullet lists. No fluff. Speak directly to the creator as "you."

**What's Landing**
What patterns are driving the top videos? Be specific — mention titles, numbers, and what they have in common.

**What's Not Working**
Where is performance falling flat and why? Be honest.

**Your Best Move**
One strategic shift that would have the biggest impact on growth right now.

**Quick Win**
One specific thing they can do this week — a video idea, title format, or posting change — based directly on what the data shows.

Keep the whole response under 250 words. Be concrete, not generic."""


def generate_insights(stats):
    """
    Generate AI insights from combined stats dict.
    stats format: { 'youtube': {...}, 'tiktok': {...} }
    Returns plain text string, or empty string if no data.
    """
    api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        return ''

    prompt = _build_prompt(stats)
    if not prompt:
        return ''

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=600,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text.strip()
