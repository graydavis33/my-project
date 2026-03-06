"""
reminder.py
Calculates overdue clients and formats the weekly reminder Slack message.
"""

from datetime import datetime, date
from config import STAGE_REMINDER_DAYS


def _days_since(date_str: str) -> int:
    """Return number of days since the given YYYY-MM-DD date string."""
    if not date_str:
        return 0
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - d).days
    except ValueError:
        return 0


def _days_until(date_str: str) -> int:
    """Return days until a due date (negative = past due)."""
    if not date_str:
        return 999
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (d - date.today()).days
    except ValueError:
        return 999


def get_reminders(clients: list) -> list:
    """
    Return a list of reminder dicts for clients that need follow-up.
    Each dict has: client_name, stage, reason
    """
    reminders = []

    for c in clients:
        stage = c.get("stage", "")
        name = c.get("name", "Unknown")
        stage_days = _days_since(c.get("stage_date", ""))
        due_days = _days_until(c.get("due_date", ""))

        threshold = STAGE_REMINDER_DAYS.get(stage, 0)

        if stage in ("Contracted", "In Production"):
            # Remind if past due date
            if due_days < 0:
                reminders.append({
                    "client": name,
                    "stage": stage,
                    "reason": f"Past due by {abs(due_days)} day(s)",
                    "urgency": "high",
                })
            elif due_days <= 3:
                reminders.append({
                    "client": name,
                    "stage": stage,
                    "reason": f"Due in {due_days} day(s)",
                    "urgency": "medium",
                })
        elif threshold > 0 and stage_days >= threshold:
            reminders.append({
                "client": name,
                "stage": stage,
                "reason": f"No update in {stage_days} day(s) (threshold: {threshold}d)",
                "urgency": "low" if stage_days < threshold * 2 else "medium",
            })

    # Sort: high urgency first
    priority = {"high": 0, "medium": 1, "low": 2}
    reminders.sort(key=lambda r: priority.get(r["urgency"], 3))
    return reminders


def format_slack_blocks(reminders: list, all_clients: list) -> list:
    """Build Slack blocks for the weekly CRM reminder."""
    today = datetime.now().strftime("%A, %B %-d")
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📋 CRM Weekly Reminder — {today}"},
        },
        {"type": "divider"},
    ]

    # Pipeline summary
    from config import PIPELINE_STAGES
    stage_counts = {s: 0 for s in PIPELINE_STAGES}
    for c in all_clients:
        s = c.get("stage", "")
        if s in stage_counts:
            stage_counts[s] += 1

    summary_parts = [f"*{s}*: {stage_counts[s]}" for s in PIPELINE_STAGES if stage_counts[s] > 0]
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": "📊 *Pipeline Overview*\n" + "  |  ".join(summary_parts)},
    })
    blocks.append({"type": "divider"})

    # Reminders
    if not reminders:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "✅ *No overdue follow-ups.* All clients are on track."},
        })
    else:
        urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        reminder_lines = "\n".join(
            f"{urgency_emoji.get(r['urgency'], '⚪')} *{r['client']}* — _{r['stage']}_ — {r['reason']}"
            for r in reminders
        )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"⚠️ *Follow-ups Needed ({len(reminders)})*\n{reminder_lines}"},
        })

    return blocks
