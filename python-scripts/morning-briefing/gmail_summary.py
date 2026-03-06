"""
gmail_summary.py
Reads pending_drafts.json from the Email Agent to surface emails needing a reply.
No API calls — just reads the JSON file directly.
"""

import json
import os
import time
from config import EMAIL_AGENT_DIR

_DRAFT_TTL_SECONDS = 7 * 24 * 3600


def get_pending_emails():
    """
    Return a list of dicts with email subject + sender for all pending drafts.
    Returns empty list if EMAIL_AGENT_DIR is not configured or file doesn't exist.
    """
    if not EMAIL_AGENT_DIR:
        return []

    drafts_file = os.path.join(EMAIL_AGENT_DIR, "pending_drafts.json")
    if not os.path.exists(drafts_file):
        return []

    try:
        with open(drafts_file) as f:
            data = json.load(f)
    except Exception:
        return []

    cutoff = time.time() - _DRAFT_TTL_SECONDS
    pending = []
    for entry in data.values():
        if entry.get("created_at", 0) < cutoff:
            continue
        email = entry.get("email", {})
        pending.append({
            "from": email.get("from", "Unknown"),
            "subject": email.get("subject", "(no subject)"),
        })

    return pending
