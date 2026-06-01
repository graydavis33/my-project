"""
followup_tracker.py
Tracks emails where Gray sent a reply and alerts via Slack if the
recipient hasn't responded after FOLLOWUP_DAYS days.

How it works:
  1. When Gray approves a reply in Slack, record_sent_reply() logs the thread.
  2. Each hourly check calls check_followups(), which scans for threads where:
     - Gray's reply is 3+ days old
     - The last message in the thread still has the SENT label (no reply yet)
  3. A single Slack alert is sent per thread — never spams.
"""

import json
import os
import time

_TRACKER_FILE = os.path.join(os.path.dirname(__file__), "followup_tracker.json")
FOLLOWUP_DAYS = 3


def record_sent_reply(email):
    """Log that Gray sent a reply to this email's thread."""
    data = _load()
    data[email["thread_id"]] = {
        "thread_id": email["thread_id"],
        "recipient":  email["from"],
        "subject":    email["subject"],
        "sent_at":    time.time(),
        "alerted":    False,
    }
    _save(data)


def check_followups(service):
    """
    Check all tracked threads for unanswered replies.
    Returns a list of overdue entries (dicts with recipient, subject, sent_at).
    Marks each alerted entry so we only notify once per thread.
    Also removes threads where the recipient has since replied.
    """
    data = _load()
    if not data:
        return []

    cutoff = time.time() - FOLLOWUP_DAYS * 86400
    overdue = []

    for thread_id, entry in list(data.items()):
        if entry.get("alerted"):
            continue
        if entry["sent_at"] > cutoff:
            continue  # not old enough yet

        try:
            thread = service.users().threads().get(
                userId="me", id=thread_id, format="metadata"
            ).execute()
            messages = thread.get("messages", [])
            if not messages:
                continue

            last_msg = messages[-1]
            label_ids = last_msg.get("labelIds", [])

            if "SENT" in label_ids:
                # Our message is still the last one — no reply received
                overdue.append(entry)
                data[thread_id]["alerted"] = True
            else:
                # Recipient replied — stop tracking this thread
                del data[thread_id]

        except Exception:
            pass

    _save(data)
    _cleanup(data)
    return overdue


def _load():
    if not os.path.exists(_TRACKER_FILE):
        return {}
    try:
        with open(_TRACKER_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    try:
        with open(_TRACKER_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _cleanup(data):
    """Remove entries older than 30 days so the tracker file stays small."""
    cutoff = time.time() - 30 * 86400
    stale = [k for k, v in data.items() if v.get("sent_at", 0) < cutoff]
    for k in stale:
        del data[k]
    if stale:
        _save(data)
