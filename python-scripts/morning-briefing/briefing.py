"""
briefing.py
Assembles all data sections into a single Slack message blocks payload.
"""

from datetime import datetime
from config import DAILY_PRIORITIES


def build_briefing_blocks(pending_emails, outstanding_invoices, top_video):
    """
    Build Slack blocks for the morning briefing message.
    Returns a list of Slack block objects.
    """
    today = datetime.now().strftime("%A, %B %-d")  # e.g. "Monday, March 5"
    blocks = []

    # ── Header ──────────────────────────────────────────────────────────────
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"☀️  Good morning, Gray — {today}"},
    })
    blocks.append({"type": "divider"})

    # ── Emails Section ───────────────────────────────────────────────────────
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

    # ── Invoices Section ─────────────────────────────────────────────────────
    if outstanding_invoices:
        inv_lines = "\n".join(
            f"• Invoice #{i['invoice_num']} — *{i['client']}* — ${i['total']} (due {i['due_date']}) — _{i['status']}_"
            for i in outstanding_invoices[:5]
        )
        if len(outstanding_invoices) > 5:
            inv_lines += f"\n_+{len(outstanding_invoices) - 5} more_"
        inv_text = f"*💸 Outstanding Invoices ({len(outstanding_invoices)})*\n{inv_lines}"
    elif outstanding_invoices is not None:
        inv_text = "*💸 Outstanding Invoices*\n_All invoices paid. You're clear._"
    else:
        inv_text = "*💸 Outstanding Invoices*\n_Invoice sheet not connected._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": inv_text}})
    blocks.append({"type": "divider"})

    # ── Top Video Section ────────────────────────────────────────────────────
    if top_video:
        video_text = (
            f"*📈 Top Video This Week*\n"
            f"• \"{top_video['title']}\" — {top_video['views']} views ({top_video['tab']})"
        )
    else:
        video_text = "*📈 Top Video This Week*\n_Analytics sheet not connected._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": video_text}})
    blocks.append({"type": "divider"})

    # ── Priorities Section ───────────────────────────────────────────────────
    priorities_text = "*✅ Today's Priorities*\n" + "\n".join(
        f"{i + 1}. {p}" for i, p in enumerate(DAILY_PRIORITIES)
    )
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": priorities_text}})

    return blocks
