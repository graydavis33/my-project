"""
news_summary.py
Fetches top headlines and AI news via free RSS feeds.
Uses Claude Haiku to write a clean AI news digest paragraph.
No API key needed for news — RSS is free and public.
"""

import logging
import feedparser
import anthropic
from config import ANTHROPIC_API_KEY

log = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_GENERAL_FEEDS = [
    ("BBC", "http://feeds.bbci.co.uk/news/rss.xml"),
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
]

_AI_FEEDS = [
    ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("VentureBeat", "https://venturebeat.com/category/ai/feed/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("Wired", "https://www.wired.com/feed/rss"),
]

_AI_DIGEST_SYSTEM = (
    "You write a daily tech and AI bulletin for Gray Davis — a freelance videographer, content creator, "
    "and AI operator building automation tools. He works in video production, social media content, "
    "and uses Claude Code daily to build Python tools and web apps.\n\n"
    "Given today's tech headlines, produce 5-7 bullet points covering:\n"
    "- New products launching (physical hardware, software, apps, AI tools)\n"
    "- AI use cases for creators, builders, and indie operators — not just enterprise news\n"
    "- Anything relevant to video production, content creation, social media, or automation\n"
    "- Interesting new technology (robotics, wearables, creative tools, dev tools)\n\n"
    "Format: bullet points only. Each bullet is one punchy sentence. No headers, no prose paragraphs. "
    "Skip big-company earnings, politics, and anything about invoices or email tools. "
    "Lead with the most interesting or useful thing for someone who builds with AI daily."
)


def _fetch_items(feeds: list, max_per_feed: int = 5) -> list:
    items = []
    for source, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                items.append({
                    "source": source,
                    "title": entry.get("title", "").strip(),
                    "summary": entry.get("summary", "")[:300].strip(),
                })
        except Exception as e:
            log.warning(f"Failed to fetch feed {source}: {e}")
    return items


def get_news_digest() -> dict:
    """
    Returns:
      top_headlines — list of {source, title} for the top general news stories
      ai_digest     — Claude-written paragraph about today's AI news (or None on failure)
    """
    # General headlines
    general_items = _fetch_items(_GENERAL_FEEDS, max_per_feed=4)
    top_headlines = [{"source": i["source"], "title": i["title"]} for i in general_items[:6]]

    # AI digest
    ai_items = _fetch_items(_AI_FEEDS, max_per_feed=5)

    if not ai_items:
        log.warning("No AI feed items fetched — skipping AI digest.")
        return {"top_headlines": top_headlines, "ai_digest": None}

    stories_text = "\n".join(
        f"[{i['source']}] {i['title']}: {i['summary']}"
        for i in ai_items[:12]
        if i["title"]
    )

    try:
        response = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=_AI_DIGEST_SYSTEM,
            messages=[{"role": "user", "content": f"Today's AI headlines:\n\n{stories_text}"}],
        )
        ai_digest = response.content[0].text.strip()
        log.info("AI digest generated successfully.")
    except Exception as e:
        log.warning(f"AI digest generation failed: {e}")
        ai_digest = None

    return {"top_headlines": top_headlines, "ai_digest": ai_digest}
