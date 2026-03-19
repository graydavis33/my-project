"""
payment_scanner.py
Uses Claude AI (Haiku) to detect income payments from Gmail notification emails.
Handles: Venmo, Stripe, Zelle (PrimeSouth Bank), QuickBooks, PayPal, Cash App, Direct Deposit.

Processes emails in batches of 5 to minimize API calls.
Sends a Slack notification to #payments for each confirmed payment.
"""

import json
import os
import anthropic
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import ANTHROPIC_API_KEY, SLACK_BOT_TOKEN, SLACK_PAYMENTS_CHANNEL_ID, LARGE_PAYMENT_THRESHOLD

SCANNED_IDS_FILE = os.path.join(os.path.dirname(__file__), '.scanned_payment_ids.json')
_BATCH_SIZE = 5

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = f"""You are a bookkeeping assistant for Gray Davis, a freelance videographer.
Your job is to detect emails where someone sent money TO Gray Davis.

For each email, extract:
- is_payment: true if this is genuinely money received by Gray, false otherwise
- amount: dollar amount received as a number (no $ sign, digits and decimal only)
- payer_name: the name of the person or company who sent the money (name only, no extra text)
- platform: one of: Venmo, Stripe, Zelle, QuickBooks, PayPal, Cash App, Direct Deposit, Other
- date: the payment date in MM/DD/YYYY format
- notes: a short note ONLY if something is unusual — e.g. amount >= ${LARGE_PAYMENT_THRESHOLD:,}, first payment from this person, irregular source, or anything that stands out. Empty string for normal routine payments.

Rules:
- is_payment must be false for: money Gray sent out, refunds, promotional emails, account alerts
- If you cannot find the amount with confidence, return null for the whole record
- Always return valid JSON only — no extra text"""

BATCH_PROMPT = """Determine if each of the following {n} emails is a payment received by Gray Davis.
Return a JSON array of exactly {n} items (one per email, in order).
Each item is either a JSON object or null if it is NOT a payment received.

Format for each item:
{{
  "is_payment": true,
  "amount": 0.00,
  "payer_name": "Name Here",
  "platform": "Venmo",
  "date": "MM/DD/YYYY",
  "notes": ""
}}

{emails}

Return ONLY the JSON array — no other text."""

SINGLE_PROMPT = """Is this a payment received by Gray Davis?

From: {sender}
Subject: {subject}
Date received: {date}

Email body:
{body}

Return ONLY a JSON object in this exact format if it IS a payment received:
{{
  "is_payment": true,
  "amount": 0.00,
  "payer_name": "Name Here",
  "platform": "Venmo",
  "date": "MM/DD/YYYY",
  "notes": ""
}}

If this is NOT a payment received, return: null"""


# ── Deduplication ────────────────────────────────────────────────────────────

def _load_scanned_ids():
    if os.path.exists(SCANNED_IDS_FILE):
        try:
            with open(SCANNED_IDS_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def _save_scanned_ids(ids):
    with open(SCANNED_IDS_FILE, 'w') as f:
        json.dump(list(ids), f)


# ── Gmail fetch ──────────────────────────────────────────────────────────────

def fetch_payment_emails(service, days=30):
    """
    Search Gmail for payment notification emails from the last N days.
    Targets Venmo, Stripe, Zelle (PrimeSouth Bank), QuickBooks, PayPal, Cash App.
    Returns a list of parsed email dicts.
    """
    query = (
        f"newer_than:{days}d "
        "(from:venmo.com OR from:stripe.com OR from:paypal.com "
        "OR from:primesouthbank.com OR from:email.primesouthbank.com "
        "OR from:quickbooks.intuit.com OR from:intuit.com "
        "OR from:cash.app OR from:square.com "
        "OR subject:zelle) "
        "(subject:\"you received\" OR subject:\"payment received\" "
        "OR subject:\"paid you\" OR subject:\"money received\" "
        "OR subject:\"invoice paid\" OR subject:\"deposit received\" "
        "OR subject:\"transferred you\" OR subject:\"direct deposit\" "
        "OR subject:\"payment from\") "
        "-from:me"
    )

    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=100)
        .execute()
    )
    messages = result.get("messages", [])

    emails = []
    for msg in messages:
        detail = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        parsed = _parse_email(detail)
        if parsed:
            emails.append(parsed)

    return emails


def _parse_email(raw_message):
    try:
        headers = {h["name"]: h["value"] for h in raw_message["payload"]["headers"]}
        body = _extract_body(raw_message["payload"])
        return {
            "id": raw_message["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "date": headers.get("Date", ""),
            "body": body,
        }
    except Exception:
        return None


def _extract_body(payload):
    import base64
    from html.parser import HTMLParser

    class _Stripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self._parts = []
        def handle_data(self, data):
            self._parts.append(data)
        def text(self):
            return " ".join(self._parts).strip()

    mime = payload.get("mimeType", "")

    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    if mime == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            p = _Stripper()
            p.feed(html)
            return p.text()

    if "parts" in payload:
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result

    return ""


# ── Claude extraction ────────────────────────────────────────────────────────

def _format_email_for_batch(i, email):
    return (
        f"--- Email {i} ---\n"
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n"
        f"Date received: {email['date']}\n"
        f"Body:\n{email['body'][:1500]}\n"
    )


def _batch_extract_payments(emails):
    """
    Send up to _BATCH_SIZE emails in one Claude Haiku call.
    Returns a list of result dicts (or None) in the same order as input.
    Falls back to individual extraction if batch parse fails.
    """
    n = len(emails)
    emails_text = "\n".join(_format_email_for_batch(i + 1, e) for i, e in enumerate(emails))
    prompt = BATCH_PROMPT.format(n=n, emails=emails_text)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300 * n,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        results = json.loads(text)
        if isinstance(results, list) and len(results) == n:
            validated = []
            for r in results:
                if r is None or not isinstance(r, dict):
                    validated.append(None)
                    continue
                if not r.get("is_payment") or not r.get("amount") or not r.get("payer_name"):
                    validated.append(None)
                    continue
                validated.append(r)
            return validated
    except (json.JSONDecodeError, Exception):
        pass

    print("    ⚠️  Batch parse failed, falling back to individual extraction...")
    return [_single_extract_payment(e) for e in emails]


def _single_extract_payment(email):
    """Fallback: extract payment data from a single email."""
    prompt = SINGLE_PROMPT.format(
        sender=email["from"],
        subject=email["subject"],
        date=email["date"],
        body=email["body"][:2000],
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    if text.lower() == "null" or not text:
        return None

    try:
        data = json.loads(text)
        if not data or not data.get("is_payment") or not data.get("amount"):
            return None
        return data
    except json.JSONDecodeError:
        return None


# ── Slack notification ───────────────────────────────────────────────────────

def _post_slack_notification(payment):
    """Post a payment received notification to #payments. Skips silently if Slack not configured."""
    if not SLACK_BOT_TOKEN or not SLACK_PAYMENTS_CHANNEL_ID:
        return

    try:
        slack = WebClient(token=SLACK_BOT_TOKEN)
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "💰 Payment Received"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Amount:*\n${payment['amount']:,.2f}"},
                    {"type": "mrkdwn", "text": f"*From:*\n{payment['payer_name']}"},
                    {"type": "mrkdwn", "text": f"*Platform:*\n{payment['platform']}"},
                    {"type": "mrkdwn", "text": f"*Date:*\n{payment['date']}"},
                ],
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "✓ Logged to Google Sheets — Business Finance Tracker"}
                ],
            },
        ]
        slack.chat_postMessage(
            channel=SLACK_PAYMENTS_CHANNEL_ID,
            blocks=blocks,
            text=f"Payment received — ${payment['amount']:,.2f} from {payment['payer_name']} via {payment['platform']}",
        )
    except SlackApiError as e:
        print(f"    ⚠️  Slack error: {e.response['error']}")


# ── Main public function ─────────────────────────────────────────────────────

def scan_payments(emails):
    """
    Detect income payments from a list of Gmail emails.
    Skips already-processed emails, batches Claude calls 5 at a time,
    posts Slack notifications, and returns transaction dicts ready for Google Sheets.
    """
    scanned_ids = _load_scanned_ids()
    transactions = []
    newly_scanned = set()

    unscanned = [e for e in emails if e['id'] not in scanned_ids]
    skipped = len(emails) - len(unscanned)
    if skipped:
        print(f"  Skipping {skipped} already-scanned email(s).")

    if not unscanned:
        return transactions

    for batch_start in range(0, len(unscanned), _BATCH_SIZE):
        batch = unscanned[batch_start:batch_start + _BATCH_SIZE]
        print(f"  Processing batch of {len(batch)} email(s) (API call {batch_start // _BATCH_SIZE + 1})...")

        results = _batch_extract_payments(batch)

        for email, result in zip(batch, results):
            newly_scanned.add(email['id'])
            if result:
                transaction = {
                    "date": result["date"],
                    "description": result["payer_name"],
                    "source": result["platform"],
                    "amount": result["amount"],
                    "notes": result.get("notes", ""),
                }
                transactions.append(transaction)
                _post_slack_notification(result)
                print(f"    ✓ {email['subject'][:50]} → ${result['amount']} from {result['payer_name']} via {result['platform']}")
            else:
                print(f"    – {email['subject'][:50]} → not a payment")

    if newly_scanned:
        _save_scanned_ids(scanned_ids | newly_scanned)

    return transactions
