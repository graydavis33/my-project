"""
onboarding_emailer.py
Sends the contract PDF and project brief to the client via Gmail.
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

from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GMAIL_SCOPES, GSPREAD_SCOPES, YOUR_NAME

ALL_SCOPES = GMAIL_SCOPES + GSPREAD_SCOPES


def get_gmail_service():
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


def send_onboarding_email(service, details: dict, contract_pdf_path: str, brief_text: str):
    """
    Email the client their contract PDF and project brief.
    """
    msg = MIMEMultipart()
    msg["to"] = details["client_email"]
    msg["subject"] = f"Welcome aboard, {details['client_name'].split()[0]}! — Contract & Project Brief"

    body = (
        f"Hi {details['client_name'].split()[0]},\n\n"
        f"Excited to work with you on your {details['project_type']} project!\n\n"
        f"I've attached your contract for review and signing. "
        f"Please sign and return it along with the 50% deposit to lock in your dates.\n\n"
        f"PROJECT BRIEF\n"
        f"{'=' * 40}\n"
        f"{brief_text}\n"
        f"{'=' * 40}\n\n"
        f"Let me know if you have any questions!\n\n"
        f"{YOUR_NAME}"
    )
    msg.attach(MIMEText(body, "plain"))

    # Attach contract PDF
    with open(contract_pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{os.path.basename(contract_pdf_path)}"',
    )
    msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
