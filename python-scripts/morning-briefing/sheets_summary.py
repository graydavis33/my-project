"""
sheets_summary.py
Reads from Invoice System and Analytics Google Sheets to surface:
- Outstanding invoices (status != "Paid")
- Top YouTube video this week
"""

from config import INVOICE_SHEET_ID, ANALYTICS_SHEET_ID
from google_auth import get_google_service


def _get_sheets_service():
    return get_google_service("sheets", "v4")


def get_outstanding_invoices():
    """
    Return list of dicts {client, total, due_date} for unpaid invoices.
    Returns empty list if INVOICE_SHEET_ID is not set.
    """
    if not INVOICE_SHEET_ID:
        return []
    try:
        service = _get_sheets_service()
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=INVOICE_SHEET_ID, range="Invoices!A2:G")
            .execute()
        )
        rows = result.get("values", [])
        # Expected columns: Invoice#, Client, Email, Date, Due Date, Status, Total
        outstanding = []
        for row in rows:
            if len(row) < 6:
                continue
            status = row[5].strip().lower() if len(row) > 5 else ""
            if status not in ("paid", ""):
                outstanding.append({
                    "invoice_num": row[0] if len(row) > 0 else "?",
                    "client": row[1] if len(row) > 1 else "?",
                    "due_date": row[4] if len(row) > 4 else "?",
                    "total": row[6] if len(row) > 6 else "?",
                    "status": row[5] if len(row) > 5 else "Sent",
                })
        return outstanding
    except Exception:
        return []


def get_top_video_this_week():
    """
    Return the top-performing video this week from the Analytics sheet.
    Returns None if ANALYTICS_SHEET_ID is not set or on error.
    """
    if not ANALYTICS_SHEET_ID:
        return None
    try:
        service = _get_sheets_service()
        # Try YouTube Shorts tab first, then Longform
        for tab in ("YouTube Shorts", "YouTube Longform"):
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=ANALYTICS_SHEET_ID, range=f"'{tab}'!A2:E11")
                .execute()
            )
            rows = result.get("values", [])
            if rows:
                # First row is top video (sheet is sorted by views desc)
                row = rows[0]
                return {
                    "title": row[0] if len(row) > 0 else "Unknown",
                    "views": row[2] if len(row) > 2 else "?",
                    "tab": tab,
                }
        return None
    except Exception:
        return None
