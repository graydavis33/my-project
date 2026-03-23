"""
sheets_client.py
Handles all Google Sheets interactions:
  - Authentication
  - Creating/finding worksheet tabs
  - Appending rows to Transactions and Business Expenses tabs
  - Reading data for the Tax Summary tab
"""

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

from config import (
    GMAIL_CREDENTIALS_PATH,
    GMAIL_TOKEN_PATH,
    GSPREAD_SCOPES,
    GMAIL_SCOPES,
    GOOGLE_SHEET_ID,
    TAB_TRANSACTIONS,
    TAB_EXPENSES,
    TAB_TAX_SUMMARY,
    TRANSACTION_HEADERS,
    EXPENSE_HEADERS,
    TAX_SUMMARY_HEADERS,
    CATEGORIES,
)

ALL_SCOPES = GMAIL_SCOPES + GSPREAD_SCOPES


def get_credentials():
    """Authenticate and return Google OAuth2 credentials (works for both Gmail and Sheets)."""
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


def get_sheet():
    """Return the main Google Sheet object."""
    creds = get_credentials()
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID)


def _auto_resize(spreadsheet, ws):
    """Auto-fit all columns to match content width."""
    spreadsheet.batch_update({
        "requests": [{
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": ws.id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": ws.col_count,
                }
            }
        }]
    })


def _auto_resize_all(spreadsheet):
    """Auto-fit all columns on every worksheet in the spreadsheet."""
    for ws in spreadsheet.worksheets():
        _auto_resize(spreadsheet, ws)


def _format_currency_column(spreadsheet, ws, col_index=3):
    """Format the Amount column as $ currency (col_index is 0-based, default=3 for column D)."""
    spreadsheet.batch_update({
        "requests": [{
            "repeatCell": {
                "range": {
                    "sheetId": ws.id,
                    "startRowIndex": 1,
                    "startColumnIndex": col_index,
                    "endColumnIndex": col_index + 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "CURRENCY",
                            "pattern": "$#,##0.00",
                        }
                    }
                },
                "fields": "userEnteredFormat.numberFormat",
            }
        }]
    })


def _find_totals_row(ws):
    """Return the 1-based row index of the TOTAL row, or None if not found."""
    col_a = ws.col_values(1)
    for i, val in enumerate(col_a):
        if val == "TOTAL":
            return i + 1
    return None


def _format_totals_row(spreadsheet, ws, row_idx):
    """Apply bold + gray background to the TOTAL row."""
    spreadsheet.batch_update({"requests": [{
        "repeatCell": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": row_idx - 1,
                "endRowIndex": row_idx,
                "startColumnIndex": 0,
                "endColumnIndex": 26,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
                    "textFormat": {"bold": True},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    }]})


def _place_totals_row_at_bottom(spreadsheet, ws):
    """
    Remove any existing TOTAL row and place a fresh one just below the last data row.
    New rows are inserted before the TOTAL row, so Google Sheets auto-expands the SUM.
    """
    existing = _find_totals_row(ws)
    if existing:
        ws.delete_rows(existing)

    all_vals = ws.get_all_values()
    last_data_row = 1
    for i, row in enumerate(all_vals):
        if any(cell.strip() for cell in row):
            last_data_row = i + 1

    target_row = last_data_row + 1
    ws.insert_row(["TOTAL", "", "", '=SUMIF(A2:A1000,"<>TOTAL",D2:D1000)', ""], index=target_row, value_input_option="USER_ENTERED")
    _format_totals_row(spreadsheet, ws, target_row)


def _insert_before_totals(ws, row_data):
    """Insert a data row just above the TOTAL row, bumping it down. Falls back to append."""
    total_row = _find_totals_row(ws)
    if total_row:
        ws.insert_row(row_data, index=total_row)
    else:
        ws.append_row(row_data)


def _freeze_rows(spreadsheet, ws, count=1):
    """Freeze the top N rows (default: header only)."""
    spreadsheet.batch_update({"requests": [{
        "updateSheetProperties": {
            "properties": {
                "sheetId": ws.id,
                "gridProperties": {"frozenRowCount": count},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    }]})


def _expand_sheet_dimensions(spreadsheet, ws, rows=1000, cols=26):
    """Ensure a worksheet has at least the given number of rows and columns."""
    requests = []
    if ws.row_count < rows:
        requests.append({"appendDimension": {"sheetId": ws.id, "dimension": "ROWS", "length": rows - ws.row_count}})
    if ws.col_count < cols:
        requests.append({"appendDimension": {"sheetId": ws.id, "dimension": "COLUMNS", "length": cols - ws.col_count}})
    if requests:
        spreadsheet.batch_update({"requests": requests})


def _expense_cols(category):
    """
    Return (vendor_col, amount_col) as 1-based column indices for a given expense category.
    Layout: [Category | Amount | spacer] per category, then Total.
    Category i → vendor_col = i*3+1, amount_col = i*3+2.
    """
    try:
        idx = CATEGORIES.index(category)
    except ValueError:
        idx = len(CATEGORIES) - 1  # fallback to last category (Other)
    return idx * 3 + 1, idx * 3 + 2


def _col_letter(col_1based):
    """Convert 1-based column number to a column letter (1→A, 2→B, etc.)"""
    return chr(ord('A') + col_1based - 1)


def get_or_create_worksheet(sheet, title, headers):
    """Return the worksheet with the given title, creating it with headers if it doesn't exist."""
    try:
        ws = sheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows=1000, cols=26)
        ws.append_row(headers)
    return ws


def setup_sheet():
    """
    Create Transactions, Business Expenses, and Tax Summary tabs with correct headers.
    Deletes Invoices and Invoice Line Items tabs if they exist (legacy cleanup).
    Safe to run multiple times — won't duplicate headers.
    """
    sheet = get_sheet()

    # Remove legacy tabs if present
    for legacy_tab in ["Invoices", "Invoice Line Items"]:
        try:
            ws = sheet.worksheet(legacy_tab)
            sheet.del_worksheet(ws)
            print(f"  Removed legacy tab: {legacy_tab}")
        except gspread.WorksheetNotFound:
            pass

    # Reset Transactions tab if headers are outdated (clears old-format data)
    try:
        ws_existing = sheet.worksheet(TAB_TRANSACTIONS)
        if ws_existing.row_values(1) != TRANSACTION_HEADERS:
            sheet.del_worksheet(ws_existing)
            print("  Reset Transactions tab (headers updated, old data cleared)")
    except gspread.WorksheetNotFound:
        pass

    # Reset Business Expenses tab if headers are outdated (old row-based format → new column format)
    try:
        ws_existing = sheet.worksheet(TAB_EXPENSES)
        if ws_existing.row_values(1) != EXPENSE_HEADERS:
            sheet.del_worksheet(ws_existing)
            print("  Reset Business Expenses tab (new side-by-side category layout)")
    except gspread.WorksheetNotFound:
        pass

    ws_tx = get_or_create_worksheet(sheet, TAB_TRANSACTIONS, TRANSACTION_HEADERS)
    ws_exp = get_or_create_worksheet(sheet, TAB_EXPENSES, EXPENSE_HEADERS)
    ws_tax = get_or_create_worksheet(sheet, TAB_TAX_SUMMARY, TAX_SUMMARY_HEADERS)

    # Expand all tabs to full spreadsheet dimensions (1000 rows x 26 cols)
    for ws in [ws_tx, ws_exp, ws_tax]:
        _expand_sheet_dimensions(sheet, ws)

    # Transactions: place TOTAL row and freeze header
    _place_totals_row_at_bottom(sheet, ws_tx)
    _freeze_rows(sheet, ws_tx, count=1)
    # Business Expenses: just freeze header (no TOTAL row — Tax Summary handles totals)
    _freeze_rows(sheet, ws_exp, count=1)

    # Always rebuild Tax Summary
    ws_tax.clear()
    ws_tax.append_row(TAX_SUMMARY_HEADERS)
    tx = TAB_TRANSACTIONS
    exp = TAB_EXPENSES

    tax_rows = []

    # Total Income
    tax_rows.append(["Total Income", f"=SUMIF('{tx}'!A:A,\"<>TOTAL\",'{tx}'!D:D)"])

    # Each expense category — amount col is i*3+2 (1-based): B, E, H, K, N
    for i, cat in enumerate(CATEGORIES):
        amount_col = _col_letter(i * 3 + 2)
        tax_rows.append([cat, f"=SUM('{exp}'!{amount_col}2:{amount_col}1000)"])

    # Total Expenses = sum of all category amount columns
    all_sums = "+".join(
        [f"SUM('{exp}'!{_col_letter(i * 3 + 2)}2:{_col_letter(i * 3 + 2)}1000)"
         for i in range(len(CATEGORIES))]
    )
    tax_rows.append(["Total Expenses", f"={all_sums}"])

    # Net Profit
    income_row = 2
    expenses_row = 2 + len(CATEGORIES) + 1
    tax_rows.append(["Net Profit", f"=B{income_row}-B{expenses_row}"])

    for row in tax_rows:
        ws_tax.append_row(row)

    # Add ARRAYFORMULA to Total column (O2) — sums all category amount cols per row
    amount_cols = [_col_letter(i * 3 + 2) for i in range(len(CATEGORIES))]
    ranges = [f"{c}2:{c}1000" for c in amount_cols]
    sum_expr = "+".join(ranges)
    total_col_1based = (len(CATEGORIES) - 1) * 3 + 3   # col O
    array_formula = f'=ARRAYFORMULA(IF(({sum_expr})=0,"",{sum_expr}))'
    ws_exp.update_cell(2, total_col_1based, array_formula)

    # Format Amount column on Transactions
    _format_currency_column(sheet, ws_tx, col_index=3)
    # Format all Amount cols on Business Expenses (0-indexed: 1, 4, 7, 10, 13) and Total col
    for i in range(len(CATEGORIES)):
        _format_currency_column(sheet, ws_exp, col_index=i * 3 + 1)
    _format_currency_column(sheet, ws_exp, col_index=total_col_1based - 1)

    _auto_resize_all(sheet)
    print(f"  Sheet setup complete. Tabs: {TAB_TRANSACTIONS}, {TAB_EXPENSES}, {TAB_TAX_SUMMARY}")


def append_transaction(date, description, source, amount, notes=""):
    """Add one income row to the Transactions tab (inserted above TOTAL row)."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_TRANSACTIONS)
    _insert_before_totals(ws, [date, description, source, amount, notes])
    _auto_resize(sheet, ws)


def append_transactions(rows):
    """Add multiple income rows at once. Each row: [date, description, source, amount, notes]."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_TRANSACTIONS)
    for row in rows:
        _insert_before_totals(ws, row)
    _auto_resize(sheet, ws)


def append_expense(date, vendor, category, amount, notes=""):
    """Add one expense to the Business Expenses tab in the correct category column."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_EXPENSES)
    vendor_col, amount_col = _expense_cols(category)
    col_vals = ws.col_values(vendor_col)
    next_row = max(len(col_vals) + 1, 2)  # always at least row 2 (below header)
    col_a = _col_letter(vendor_col)
    col_b = _col_letter(amount_col)
    ws.update(f"{col_a}{next_row}:{col_b}{next_row}", [[vendor, amount]])
    _auto_resize(sheet, ws)


def append_expenses(rows):
    """Add multiple expense rows. Each row: [date, vendor, category, amount, notes]."""
    sheet = get_sheet()
    ws = sheet.worksheet(TAB_EXPENSES)
    for row in rows:
        _date, vendor, category, amount = row[0], row[1], row[2], row[3]
        vendor_col, amount_col = _expense_cols(category)
        col_vals = ws.col_values(vendor_col)
        next_row = max(len(col_vals) + 1, 2)
        col_a = _col_letter(vendor_col)
        col_b = _col_letter(amount_col)
        ws.update(f"{col_a}{next_row}:{col_b}{next_row}", [[vendor, amount]])
    _auto_resize(sheet, ws)
