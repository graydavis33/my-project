"""
main_lite.py
Cloud-only morning briefing — runs via GitHub Actions at 8am daily.
No Google APIs, no local files. Just the essentials sent to Slack.

Sections:
  - Weather (Open-Meteo, free, no key)
  - Quote of the Day (ZenQuotes, free, no key)
  - Top Headlines (RSS, free, no key)
  - AI Today (RSS + Claude Haiku digest)
"""

import os
import sys
import logging
from datetime import datetime
from slack_sdk import WebClient
from dotenv import load_dotenv

# Load local .env first, fall back to personal-assistant .env (shares Slack tokens)
_here = os.path.dirname(__file__)
load_dotenv(os.path.join(_here, ".env"))
load_dotenv(os.path.join(_here, "..", "personal-assistant", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# Pull directly from env (GitHub Actions injects these as env vars)
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_USER_ID = os.environ["SLACK_USER_ID"]

slack = WebClient(token=SLACK_BOT_TOKEN)


def _build_blocks(weather, quote, news):
    now = datetime.now()
    today = f"{now.strftime('%A, %B')} {now.day}"

    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"☀️  Good morning, Gray — {today}"},
    })
    blocks.append({"type": "divider"})

    # Weather
    if weather:
        precip = f" — {weather['precip']}% chance of rain" if weather["precip"] >= 30 else ""
        w_text = f"*🌤️ NYC Weather*\n{weather['description']} — {weather['temp']}°F{precip}"
    else:
        w_text = "*🌤️ NYC Weather*\n_Could not fetch weather._"
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": w_text}})
    blocks.append({"type": "divider"})

    # Quote
    if quote:
        q_text = f"*💭 Quote of the Day*\n\"{quote['quote']}\"\n— _{quote['author']}_"
    else:
        q_text = "*💭 Quote of the Day*\n_Stay focused. Make it count._"
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": q_text}})
    blocks.append({"type": "divider"})

    # Headlines
    if news and news.get("top_headlines"):
        lines = "\n".join(f"• [{h['source']}] {h['title']}" for h in news["top_headlines"])
        h_text = f"*🌍 Today's Headlines*\n{lines}"
    else:
        h_text = "*🌍 Today's Headlines*\n_Could not fetch headlines._"
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": h_text}})
    blocks.append({"type": "divider"})

    # AI digest
    if news and news.get("ai_digest"):
        ai_text = f"*🤖 AI Today*\n{news['ai_digest']}"
    else:
        ai_text = "*🤖 AI Today*\n_Could not fetch AI news._"
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": ai_text}})

    return blocks


def send_briefing():
    log.info("Assembling lite morning briefing...")

    from weather_summary import get_weather
    from quote_summary import get_daily_quote
    from news_summary import get_news_digest

    weather = get_weather()
    log.info(f"  Weather: {weather['temp']}°F" if weather else "  Weather: failed")

    quote = get_daily_quote()
    log.info(f"  Quote: {quote['author']}" if quote else "  Quote: failed")

    news = get_news_digest()
    log.info(f"  Headlines: {len(news.get('top_headlines', []))} | AI digest: {'yes' if news.get('ai_digest') else 'no'}")

    blocks = _build_blocks(weather, quote, news)

    slack.chat_postMessage(
        channel=SLACK_USER_ID,
        blocks=blocks,
        text="☀️ Good morning! Here's your daily briefing.",
    )
    log.info("Lite briefing sent.")


if __name__ == "__main__":
    try:
        send_briefing()
    except Exception:
        log.exception("Lite briefing failed")
        sys.exit(1)
