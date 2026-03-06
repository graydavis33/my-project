"""
crm_sheets.py
Google Sheets backend for the CRM.
Handles creating, reading, and updating client records.
"""

import os
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime

from config import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_TOKEN_PATH,
    GSPREAD_SCOPES,
    PIPELINE_STAGES,
)

_ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

# Sheet column indices (0-based)
COL = {
    "id":            0,
    "name":          1,
    "email":         2,
    "company":       3,
    "project":       4,
    "stage":         5,
    "budget":        6,
    "stage_date":    7,
    "due_date":      8,
    "notes":         9,
    "created_at":    10,
}
HEADERS = [
    "ID", "Client Name", "Email", "Company", "Project",
    "Stage", "Budget", "Stage Date", "Due Date", "Notes", "Created At"
]


def _get_creds():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, GSPREAD_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_PATH, GSPREAD_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def _update_env(key, value):
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


def get_sheet():
    """Return the Clients worksheet, creating the sheet if needed."""
    from config import CRM_SHEET_ID
    gc = gspread.authorize(_get_creds())

    if CRM_SHEET_ID:
        spreadsheet = gc.open_by_key(CRM_SHEET_ID)
    else:
        spreadsheet = gc.create("Client CRM — Pipeline Tracker")
        spreadsheet.share("graydavis33@gmail.com", perm_type="user", role="writer")
        _update_env("CRM_SHEET_ID", spreadsheet.id)
        print(f"  Created CRM Google Sheet: {spreadsheet.url}")

    try:
        ws = spreadsheet.worksheet("Clients")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet("Clients", rows=500, cols=len(HEADERS))
        ws.append_row(HEADERS)
        ws.format("A1:K1", {"textFormat": {"bold": True}})
        _setup_summary_tab(spreadsheet)

    return ws


def _setup_summary_tab(spreadsheet):
    """Create a Pipeline Summary tab with per-stage counts."""
    try:
        ws = spreadsheet.add_worksheet("Pipeline Summary", rows=20, cols=3)
        ws.append_row(["Stage", "Count", "Total Budget"])
        for stage in PIPELINE_STAGES:
            ws.append_row([stage, f'=COUNTIF(Clients!F:F,"{stage}")',
                           f'=SUMIF(Clients!F:F,"{stage}",Clients!G:G)'])
        ws.format("A1:C1", {"textFormat": {"bold": True}})
    except Exception:
        pass


def _next_id(ws):
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return 1
    ids = [int(r[COL["id"]]) for r in rows[1:] if r[COL["id"]].isdigit()]
    return max(ids) + 1 if ids else 1


def add_client(name, email, company, project, budget, due_date="", notes=""):
    """Add a new client at Lead stage. Returns the new client ID."""
    ws = get_sheet()
    client_id = _next_id(ws)
    today = datetime.today().strftime("%Y-%m-%d")
    ws.append_row([
        client_id, name, email, company, project,
        "Lead", budget, today, due_date, notes, today
    ])
    return client_id


def update_stage(client_id, new_stage):
    """Move a client to a new pipeline stage. Returns True if found."""
    if new_stage not in PIPELINE_STAGES:
        raise ValueError(f"Invalid stage. Choose from: {', '.join(PIPELINE_STAGES)}")
    ws = get_sheet()
    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if row[COL["id"]] == str(client_id):
            stage_col = COL["stage"] + 1  # gspread is 1-indexed
            date_col = COL["stage_date"] + 1
            ws.update_cell(i, stage_col, new_stage)
            ws.update_cell(i, date_col, datetime.today().strftime("%Y-%m-%d"))
            return True
    return False


def list_clients(stage=None):
    """Return all clients, optionally filtered by stage."""
    ws = get_sheet()
    rows = ws.get_all_values()
    clients = []
    for row in rows[1:]:
        if len(row) < len(HEADERS):
            row += [""] * (len(HEADERS) - len(row))
        client = {k: row[v] for k, v in COL.items()}
        if stage is None or client["stage"] == stage:
            clients.append(client)
    return clients


def get_all_active_clients():
    """Return all clients not in Paid stage."""
    return [c for c in list_clients() if c["stage"] != "Paid"]
