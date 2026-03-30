"""
briefing.py
Assembles all data sections into a single Slack message blocks payload.
"""

from datetime import datetime


def build_briefing_blocks(events, pending_emails, outstanding_invoices, weather, quote, news=None):
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

    # ── Calendar ─────────────────────────────────────────────────────────────
    if events:
        event_lines = "\n".join(f"• {e['time']} — {e['title']}" for e in events)
        calendar_text = f"*📅 Today's Schedule ({len(events)} event{'s' if len(events) != 1 else ''})*\n{event_lines}"
    else:
        calendar_text = "*📅 Today's Schedule*\n_Nothing on the calendar — wide open day._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": calendar_text}})
    blocks.append({"type": "divider"})

    # ── Emails ───────────────────────────────────────────────────────────────
    if pending_emails:
        email_lines = "\n".join(
            f"• *{e['subject']}* — _{e['from'].split('<')[0].strip()}_"
            for e in pending_emails[:5]
        )
        if len(pending_emails) > 5:
            email_lines += f"\n_+{len(pending_emails) - 5} more_"
        email_text = f"*📬 Emails Needing Reply ({len(pending_emails)})*\n{email_lines}"
    else:
        email_text = "*📬 Emails Needing Reply*\n_Inbox clear — no pending drafts._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": email_text}})
    blocks.append({"type": "divider"})

    # ── Invoices ─────────────────────────────────────────────────────────────
    if outstanding_invoices:
        inv_lines = "\n".join(
            f"• Invoice #{i['invoice_num']} — *{i['client']}* — ${i['total']} (due {i['due_date']}) — _{i['status']}_"
            for i in outstanding_invoices[:5]
        )
        if len(outstanding_invoices) > 5:
            inv_lines += f"\n_+{len(outstanding_invoices) - 5} more_"
        inv_text = f"*💸 Outstanding Invoices ({len(outstanding_invoices)})*\n{inv_lines}"
    else:
        inv_text = "*💸 Outstanding Invoices*\n_All invoices paid. You're clear._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": inv_text}})
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

    # ── AI Today ─────────────────────────────────────────────────────────────
    if news and news.get("ai_digest"):
        ai_text = f"*🤖 AI Today*\n{news['ai_digest']}"
    else:
        ai_text = "*🤖 AI Today*\n_Could not fetch AI news._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": ai_text}})

    return blocks
