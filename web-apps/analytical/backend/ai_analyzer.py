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
            f"YouTube: {yt.get('channel_name', '')} — {yt.get('subscriber_count', 0):,} subscribers, "
            f"{len(yt['videos'])} videos"
        )

    tt = stats.get('tiktok')
    if tt and tt.get('videos'):
        all_videos.extend(tt['videos'])
        platform_summaries.append(
            f"TikTok: {tt.get('username', '')} — {tt.get('follower_count', 0):,} followers, "
            f"{len(tt['videos'])} videos"
        )

    if not all_videos:
        return None

    total = len(all_videos)
    top = sorted(all_videos, key=lambda x: x.get('views', 0), reverse=True)[:10]
    bottom = sorted(all_videos, key=lambda x: x.get('views', 0))[:5]
    avg_views = sum(v.get('views', 0) for v in all_videos) / total

    def fmt(v):
        return (
            f"  [{v.get('platform', '')}] <title>{_safe_title(v.get('title', ''))}</title>\n"
            f"  Published: {v.get('published_at', '—')} | Views: {v.get('views', 0):,} | "
            f"Likes: {v.get('likes', 0):,} | Comments: {v.get('comments', 0):,} | "
            f"Shares: {v.get('shares', 0):,}\n"
        )

    platforms_str = '\n'.join(f'- {s}' for s in platform_summaries)

    return f"""You are a social media analytics expert advising a content creator. Analyze this cross-platform data and provide deep, actionable insights.

ACCOUNTS:
{platforms_str}

OVERVIEW:
- Total videos analyzed: {total}
- Average views per video: {avg_views:,.0f}

TOP 10 PERFORMING VIDEOS:
{''.join(fmt(v) for v in top)}
BOTTOM 5 PERFORMING VIDEOS:
{''.join(fmt(v) for v in bottom)}

Please provide a thorough analysis covering:
1. **What's Working** — Common patterns among top performers (length, topics, titles, timing, platform)
2. **What's Not Working** — Why the low performers likely underperformed
3. **Cross-Platform Patterns** — What the data reveals about YouTube vs TikTok performance
4. **Engagement Analysis** — Likes/comments/shares relative to views
5. **Top 5 Recommendations** — Specific, actionable changes to make immediately

Be specific. Reference actual video titles and numbers. Give honest, direct advice."""


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
        max_tokens=1500,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text.strip()
