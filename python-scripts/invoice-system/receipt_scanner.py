"""
receipt_scanner.py
Uses Claude AI to extract transaction data from Gmail receipt emails.
Determines: date, vendor/description, amount, and tax category.

Processes emails in batches of 5 to reduce API calls (~35% fewer tokens).
"""

import json
import os
import sys as _sys
import anthropic
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import ANTHROPIC_API_KEY, CATEGORIES, SLACK_BOT_TOKEN, SLACK_PAYMENTS_CHANNEL_ID

_sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from usage_logger import track_response

SCANNED_IDS_FILE = os.path.join(os.path.dirname(__file__), '.scanned_receipt_ids.json')
_BATCH_SIZE = 5
_LARGE_EXPENSE_THRESHOLD = 500


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


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_CATEGORY_LIST = "\n".join(f"  - {c}" for c in CATEGORIES)

SYSTEM_PROMPT = f"""You are a bookkeeping assistant. Your job is to extract business expense data
from receipt and billing emails for Gray Davis, a freelance videographer.

Given an email, extract:
- date: the transaction or billing date in MM/DD/YYYY format
- vendor: vendor/company name only (e.g. "Adobe", "Amazon", "B&H Photo")
- amount: the total charged amount as a number (no $ sign, just digits and decimal)
- category: one of these exact options:
{_CATEGORY_LIST}
- notes: a short note ONLY if the expense is unusual — e.g. amount >= ${_LARGE_EXPENSE_THRESHOLD:,}, one-time large purchase, anything that stands out. Empty string for normal routine expenses.

Rules:
- If you cannot determine the amount with confidence, return null for amount
- If the email is clearly not a receipt or payment confirmation, return null
- Always return valid JSON only — no extra text"""

BATCH_PROMPT = """Extract business expense data from each of the following {n} receipt emails.
Return a JSON array of exactly {n} items (one per email, in order).
Each item is either a JSON object with fields date/vendor/amount/category/notes, or null if not a receipt.

Format for each item:
{{
  "date": "MM/DD/YYYY",
  "vendor": "Vendor Name",
  "amount": 0.00,
  "category": "Category Name",
  "notes": ""
}}

{emails}

Return ONLY the JSON array — no other text."""

SINGLE_PROMPT = """Extract the business expense data from this receipt email.

From: {sender}
Subject: {subject}
Date received: {date}

Email body:
{body}

Return ONLY a JSON object in this exact format:
{{
  "date": "MM/DD/YYYY",
  "vendor": "Vendor Name",
  "amount": 0.00,
  "category": "Category Name",
  "notes": ""
}}

If this is not a receipt or you can't find the amount, return: null"""


def _format_email_for_batch(i, email):
    return (
        f"--- Email {i} ---\n"
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n"
        f"Date received: {email['date']}\n"
        f"Body:\n{email['body'][:1500]}\n"
    )


def _batch_extract_transactions(emails):
    """
    Send up to _BATCH_SIZE emails in one Claude call.
    Returns a list of result dicts (or None) in the same order as input.
    Falls back to individual extraction if batch parse fails.
    """
    n = len(emails)
    emails_text = "\n".join(_format_email_for_batch(i + 1, e) for i, e in enumerate(emails))
    prompt = BATCH_PROMPT.format(n=n, emails=emails_text)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400 * n,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    track_response(response)

    text = response.content[0].text.strip()

    try:
        results = json.loads(text)
        if isinstance(results, list) and len(results) == n:
            # Validate each result
            validated = []
            for r in results:
                if r is None or not isinstance(r, dict):
                    validated.append(None)
                    continue
                if not r.get("amount") or not r.get("vendor"):
                    validated.append(None)
                    continue
                if r.get("category") not in CATEGORIES:
                    r["category"] = "Other"
                validated.append(r)
            return validated
    except (json.JSONDecodeError, Exception):
        pass

    # Batch failed — fall back to individual extraction
    print("    [!] Batch parse failed, falling back to individual extraction...")
    return [_single_extract_transaction(e) for e in emails]


def _single_extract_transaction(email):
    """
    Fallback: extract transaction data from a single email.
    Returns a dict or None.
    """
    prompt = SINGLE_PROMPT.format(
        sender=email["from"],
        subject=email["subject"],
        date=email["date"],
        body=email["body"][:2000],
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    track_response(response)

    text = response.content[0].text.strip()

    if text.lower() == "null" or not text:
        return None

    try:
        data = json.loads(text)
        if not data or not data.get("amount") or not data.get("vendor"):
            return None
        if data.get("category") not in CATEGORIES:
            data["category"] = "Other"
        return data
    except json.JSONDecodeError:
        return None


def _post_slack_notification(expense):
    if not SLACK_BOT_TOKEN or not SLACK_PAYMENTS_CHANNEL_ID:
        return
    try:
        slack = WebClient(token=SLACK_BOT_TOKEN)
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "[receipt] Expense Logged"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Amount:*\n${expense['amount']:,.2f}"},
                    {"type": "mrkdwn", "text": f"*Vendor:*\n{expense['vendor']}"},
                    {"type": "mrkdwn", "text": f"*Category:*\n{expense['category']}"},
                    {"type": "mrkdwn", "text": f"*Date:*\n{expense['date']}"},
                ],
            },
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "[+] Logged to Google Sheets — Business Expenses tab"}]},
        ]
        slack.chat_postMessage(
            channel=SLACK_PAYMENTS_CHANNEL_ID,
            blocks=blocks,
            text=f"Expense logged — ${expense['amount']:,.2f} at {expense['vendor']} ({expense['category']})",
        )
    except SlackApiError as e:
        print(f"    [!]  Slack error: {e.response['error']}")


def scan_receipts(emails):
    """
    Run extraction on a list of Gmail emails in batches of 5.
    Skips emails already processed in a previous run (deduplication via ID cache).
    Returns a list of expense dicts ready to append to the Business Expenses tab.
    Each dict has: date, vendor, category, amount, notes
    """
    scanned_ids = _load_scanned_ids()
    expenses = []
    newly_scanned = set()

    unscanned = [e for e in emails if e['id'] not in scanned_ids]
    skipped = len(emails) - len(unscanned)
    if skipped:
        print(f"  Skipping {skipped} already-scanned email(s).")

    if not unscanned:
        return expenses

    for batch_start in range(0, len(unscanned), _BATCH_SIZE):
        batch = unscanned[batch_start:batch_start + _BATCH_SIZE]
        print(f"  Processing batch of {len(batch)} email(s) (API call {batch_start // _BATCH_SIZE + 1})...")

        results = _batch_extract_transactions(batch)

        for email, result in zip(batch, results):
            newly_scanned.add(email['id'])
            if result:
                expense = {
                    "date": result["date"],
                    "vendor": result["vendor"],
                    "category": result["category"],
                    "amount": result["amount"],
                    "notes": result.get("notes", ""),
                }
                expenses.append(expense)
                _post_slack_notification(expense)
                print(f"    [+] {email['subject'][:50]} -> ${result['amount']} | {result['category']}")
            else:
                print(f"    - {email['subject'][:50]} -> not a receipt")

    if newly_scanned:
        _save_scanned_ids(scanned_ids | newly_scanned)

    return expenses
