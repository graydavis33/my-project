"""
receipt_scanner.py
Uses Claude AI to extract transaction data from Gmail receipt emails.
Determines: date, vendor/description, amount, and tax category.
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, CATEGORIES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a bookkeeping assistant. Your job is to extract transaction data
from receipt and billing emails.

Given an email, extract:
- date: the transaction or billing date (YYYY-MM-DD format)
- description: vendor name + brief description (e.g. "Adobe Creative Cloud - Monthly Subscription")
- amount: the total charged amount as a number (no $ sign, just digits and decimal)
- category: one of these exact options:
  - Software & Subscriptions
  - Equipment & Gear
  - Advertising & Marketing
  - Contractor Payments
  - Other

Rules:
- If you cannot determine the amount with confidence, return null for amount
- If the email is clearly not a receipt or payment confirmation, return null
- Always return valid JSON only — no extra text"""

EXTRACTION_PROMPT = """Extract the transaction data from this receipt email.

From: {sender}
Subject: {subject}
Date received: {date}

Email body:
{body}

Return ONLY a JSON object in this exact format:
{{
  "date": "YYYY-MM-DD",
  "description": "Vendor - Description",
  "amount": 0.00,
  "category": "Category Name"
}}

If this is not a receipt or you can't find the amount, return: null"""


def extract_transaction(email):
    """
    Use Claude to extract transaction data from a receipt email.
    Returns a dict with date/description/amount/category, or None if not a receipt.
    """
    prompt = EXTRACTION_PROMPT.format(
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

    text = response.content[0].text.strip()

    if text.lower() == "null" or not text:
        return None

    try:
        data = json.loads(text)
        # Validate required fields
        if not data or not data.get("amount") or not data.get("description"):
            return None
        # Ensure category is valid
        if data.get("category") not in CATEGORIES:
            data["category"] = "Other"
        return data
    except json.JSONDecodeError:
        return None


def scan_receipts(emails):
    """
    Run extraction on a list of Gmail emails.
    Returns a list of transaction dicts ready to append to Google Sheets.
    Each dict has: date, description, source, category, amount, type, notes
    """
    transactions = []
    for email in emails:
        print(f"  Scanning: \"{email['subject']}\" from {email['from'][:40]}")
        result = extract_transaction(email)
        if result:
            transactions.append({
                "date": result["date"],
                "description": result["description"],
                "source": "Gmail",
                "category": result["category"],
                "amount": result["amount"],
                "type": "Expense",
                "notes": f"Gmail: {email['subject'][:60]}",
            })
            print(f"    → ${result['amount']} | {result['category']}")
        else:
            print(f"    → Skipped (not a receipt)")

    return transactions
