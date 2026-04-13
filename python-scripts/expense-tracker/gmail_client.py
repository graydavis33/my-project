"""
gmail_client.py
Gmail authentication and personal expense email fetching.
Adapted from invoice-system/gmail_client.py — Gmail readonly only.
"""

import base64
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GMAIL_SCOPES


def get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    creds = None

    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_personal_expense_emails(service, days=30):
    """
    Search Gmail for personal expense emails from the last N days.
    Returns a list of parsed email dicts: {id, from, subject, date, body}.
    """
    query = (
        f"newer_than:{days}d "
        "(subject:receipt OR subject:\"order confirmation\" OR subject:\"payment confirmation\" "
        "OR subject:subscription OR subject:renewal OR subject:charge OR subject:billing "
        "OR from:doordash.com OR from:ubereats.com OR from:grubhub.com OR from:instacart.com "
        "OR from:netflix.com OR from:spotify.com OR from:hulu.com OR from:disneyplus.com "
        "OR from:apple.com OR from:amazon.com OR from:amazon OR from:coned.com "
        "OR from:spectrum.com OR from:verizon.com OR from:att.com) "
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
    """Extract fields we need from a raw Gmail API message."""
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
    """Pull plain text body from a Gmail message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    if "parts" in payload:
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result

    return ""
