"""
gmail_client.py
Handles all Gmail API interactions:
  - Authentication
  - Fetching unprocessed emails
  - Applying the agent-processed label
  - Sending emails
"""

import base64
import json
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    GMAIL_CREDENTIALS_PATH,
    GMAIL_TOKEN_PATH,
    GMAIL_SCOPES,
    PROCESSED_LABEL,
)

# Cache label IDs so we only hit the labels.list() API once per process run
_label_cache: dict = {}


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
        with open(GMAIL_TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_or_create_label(service, label_name):
    """Return the label ID, creating the label if it doesn't exist.
    Caches all label IDs after the first API call to avoid repeated list requests."""
    if label_name in _label_cache:
        return _label_cache[label_name]

    # Populate cache from a single labels.list() call
    existing = service.users().labels().list(userId="me").execute()
    for label in existing.get("labels", []):
        _label_cache[label["name"]] = label["id"]

    if label_name in _label_cache:
        return _label_cache[label_name]

    # Label doesn't exist yet — create it
    new_label = (
        service.users()
        .labels()
        .create(userId="me", body={"name": label_name})
        .execute()
    )
    _label_cache[label_name] = new_label["id"]
    return new_label["id"]


def fetch_unprocessed_emails(service, label_id):
    """
    Fetch emails from the last 24 hours that have NOT been labeled agent-processed yet.
    Only looks at INBOX emails to avoid drafts/sent/spam.
    Handles pagination so more than 50 emails are never silently missed.
    """
    query = f"newer_than:1d -label:{PROCESSED_LABEL}"
    messages = []
    page_token = None

    while True:
        kwargs = {"userId": "me", "q": query, "labelIds": ["INBOX"], "maxResults": 50}
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.users().messages().list(**kwargs).execute()
        messages.extend(result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    emails = []
    for msg in messages:
        detail = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        emails.append(parse_email(detail))

    return emails


def parse_email(raw_message):
    """Extract the fields we care about from a raw Gmail API message."""
    headers = {h["name"]: h["value"] for h in raw_message["payload"]["headers"]}
    body = extract_body(raw_message["payload"])

    return {
        "id": raw_message["id"],
        "thread_id": raw_message["threadId"],
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "date": headers.get("Date", ""),
        "body": body,
    }


def extract_body(payload):
    """Pull plain text body out of a Gmail message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    if "parts" in payload:
        for part in payload["parts"]:
            result = extract_body(part)
            if result:
                return result

    return ""


def apply_category_label(service, message_id, label_name):
    """Apply a category label (e.g. 'Agent/Needs Reply') to an email, creating it if needed."""
    label_id = get_or_create_label(service, label_name)
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [label_id]},
    ).execute()


def mark_as_processed(service, message_id, label_id):
    """Apply the agent-processed label so this email won't be processed again."""
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [label_id]},
    ).execute()


def fetch_sent_emails(service, count=25):
    """Fetch the most recent sent emails for voice analysis."""
    result = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["SENT"], maxResults=count)
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
        parsed = parse_email(detail)
        # Only include emails with meaningful text (skips file-drop emails with just links)
        if len(parsed["body"].strip()) > 80:
            emails.append(parsed)

    return emails


def send_email(service, to, subject, body, thread_id=None):
    """Send an email from the authenticated Gmail account."""
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    payload = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id

    service.users().messages().send(userId="me", body=payload).execute()
