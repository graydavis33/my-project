"""
classifier.py
Uses Claude AI to read each email and decide:
  - needs_reply  → real person, requires a response
  - fyi_only     → informational, no reply needed
  - ignore       → newsletter, promo, receipt, social notification
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', 'shared'))
from usage_logger import track_response

import anthropic
from config import ANTHROPIC_API_KEY, CATEGORY_NEEDS_REPLY, CATEGORY_FYI_ONLY, CATEGORY_IGNORE

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an email assistant helping Gray Davis, a social media marketer.
Your job is to classify each email into one of three categories:

- needs_reply: A real person sent this and expects or would appreciate a response.
  Examples: clients asking questions, collaborators following up, business inquiries,
  personal contacts reaching out.

- fyi_only: Informational email from a real person or service that does NOT need a reply.
  Examples: shipping updates for something Gray ordered, CC'd replies, meeting confirmations.

- ignore: Automated or bulk email that should be ignored entirely.
  Examples: newsletters, promotional emails, sales/discounts, order receipts,
  Instagram/TikTok/LinkedIn notifications, Substack digests.

Respond with ONLY one of these exact words: needs_reply, fyi_only, ignore
Do not add any explanation or punctuation."""


def classify_email(email):
    """
    Pass an email to Claude and get back its category string.
    Returns one of: 'needs_reply', 'fyi_only', 'ignore'
    """
    attachment_section = ""
    if email.get("attachments"):
        parts = [f"=== {a['name']} ===\n{a['text']}" for a in email["attachments"]]
        attachment_section = "\n\nAttachments:\n" + "\n\n".join(parts)

    user_message = f"""
From: {email['from']}
Subject: {email['subject']}
Date: {email['date']}

Body:
{email['body'][:2000]}{attachment_section}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    track_response(response)

    category = response.content[0].text.strip().lower()

    if category not in (CATEGORY_NEEDS_REPLY, CATEGORY_FYI_ONLY, CATEGORY_IGNORE):
        category = CATEGORY_IGNORE

    return category
