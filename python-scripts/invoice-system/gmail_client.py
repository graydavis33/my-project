"""
gmail_client.py
Handles Gmail interactions for the invoice system:
  - Authentication (shared with sheets_client via token.json)
  - Searching for receipt emails
  - Sending invoice emails with PDF attachment
"""

import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GMAIL_SCOPES, GSPREAD_SCOPES

ALL_SCOPES = GMAIL_SCOPES + GSPREAD_SCOPES


def get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    creds = None

    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, ALL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, ALL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_receipt_emails(service, days=30):
    """
    Search Gmail for receipt/payment emails from the last N days.
    Returns a list of parsed email dicts.
    """
    query = (
        f"newer_than:{days}d "
        "(subject:receipt OR subject:\"order confirmation\" OR subject:\"payment confirmation\" "
        "OR subject:\"invoice\" OR subject:\"billing\" OR subject:\"subscription\" "
        "OR subject:\"your order\" OR subject:charge OR subject:statement "
        "OR subject:renewal OR subject:\"payment receipt\" OR subject:\"order shipped\" "
        "OR subject:purchase) "
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


def send_invoice_email(service, to_email, client_name, invoice_num, total, pdf_path):
    """
    Send an invoice email to the client with the PDF attached.
    """
    msg = MIMEMultipart()
    msg["to"] = to_email
    msg["subject"] = f"Invoice #{invoice_num} from Gray Davis"

    body = (
        f"Hi {client_name},\n\n"
        f"Please find your invoice attached (Invoice #{invoice_num} — ${total:.2f}).\n\n"
        f"Let me know if you have any questions!\n\n"
        f"Gray"
    )
    msg.attach(MIMEText(body, "plain"))

    # Attach PDF
    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="Invoice_{invoice_num}.pdf"',
    )
    msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
