"""
briefing.py
Assembles all data sections into a single Slack message blocks payload.
"""

from datetime import datetime


def build_briefing_blocks(weather, quote, news=None):
    now = datetime.now()
    today = f"{now.strftime('%A, %B')} {now.day}"
    blocks = []

    # ── Header ──────────────────────────────────────────────────────────────
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"☀️  Good morning, Gray — {today}"},
    })
    blocks.append({"type": "divider"})

    # ── Weather ──────────────────────────────────────────────────────────────
    if weather:
        precip_note = f" — {weather['precip']}% chance of rain" if weather["precip"] >= 30 else ""
        weather_text = f"*🌤️ NYC Weather*\n{weather['description']} — {weather['temp']}°F{precip_note}"
    else:
        weather_text = "*🌤️ NYC Weather*\n_Unable to fetch weather._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": weather_text}})
    blocks.append({"type": "divider"})

    # ── Quote ────────────────────────────────────────────────────────────────
    if quote:
        quote_text = f"*💭 Quote of the Day*\n\"{quote['quote']}\"\n— _{quote['author']}_"
    else:
        quote_text = "*💭 Quote of the Day*\n_Stay focused. Make it count._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": quote_text}})
    blocks.append({"type": "divider"})

    # ── Top Headlines ────────────────────────────────────────────────────────
    if news and news.get("top_headlines"):
        headline_lines = "\n".join(
            f"• [{h['source']}] {h['title']}"
            for h in news["top_headlines"]
        )
        headlines_text = f"*🌍 Today's Headlines*\n{headline_lines}"
    else:
        headlines_text = "*🌍 Today's Headlines*\n_Could not fetch headlines._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": headlines_text}})
    blocks.append({"type": "divider"})

    # ── Tech & AI ─────────────────────────────────────────────────────────────
    if news and news.get("ai_digest"):
        ai_text = f"*⚡ Tech & AI*\n{news['ai_digest']}"
    else:
        ai_text = "*⚡ Tech & AI*\n_Could not fetch tech news._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": ai_text}})

    return blocks
