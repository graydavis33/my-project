"""
sheets_tracker.py
Logs new client onboardings to a Google Sheet for tracking.
Creates the sheet and tab if they don't exist.
"""

import os
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime

from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GSPREAD_SCOPES, GMAIL_SCOPES

_ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
ALL_SCOPES = GSPREAD_SCOPES + GMAIL_SCOPES


def _get_creds():
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
    return creds


def _get_or_create_sheet():
    """Get or create the Onboarding Tracker Google Sheet."""
    from config import ONBOARDING_SHEET_ID
    gc = gspread.authorize(_get_creds())

    if ONBOARDING_SHEET_ID:
        return gc.open_by_key(ONBOARDING_SHEET_ID)

    # Create new sheet
    sheet = gc.create("Client Onboarding Tracker")
    sheet.share("graydavis33@gmail.com", perm_type="user", role="writer")

    # Save sheet ID to .env
    sheet_id = sheet.id
    _update_env("ONBOARDING_SHEET_ID", sheet_id)
    print(f"  Created Google Sheet: {sheet.url}")
    return sheet


def _update_env(key, value):
    """Append or update a key in the .env file."""
    lines = []
    found = False
    if os.path.exists(_ENV_FILE):
        with open(_ENV_FILE) as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
    if not found:
        lines.append(f"{key}={value}\n")
    with open(_ENV_FILE, "w") as f:
        f.writelines(lines)


def _setup_sheet(sheet):
    """Create the Clients tab with headers if it doesn't exist."""
    try:
        ws = sheet.worksheet("Clients")
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet("Clients", rows=500, cols=10)
        ws.append_row([
            "Date", "Client Name", "Email", "Company",
            "Project Type", "Scope", "Timeline", "Budget",
            "Status", "Notes"
        ])
        ws.format("A1:J1", {"textFormat": {"bold": True}})
    return ws


def log_client(details: dict):
    """Append a new client row to the Clients tab."""
    sheet = _get_or_create_sheet()
    ws = _setup_sheet(sheet)
    ws.append_row([
        datetime.today().strftime("%Y-%m-%d"),
        details["client_name"],
        details["client_email"],
        details.get("company", ""),
        details["project_type"],
        details["scope"],
        details["timeline"],
        details["budget"],
        "Onboarded",
        details.get("notes", ""),
    ])
