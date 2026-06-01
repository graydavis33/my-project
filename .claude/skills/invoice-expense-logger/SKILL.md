---
name: invoice-expense-logger
description: Run the Invoice & Tax Tracker workflow — scan Gmail for receipts or payments, import Venmo/bank CSVs, manually log a business expense, or create an invoice. Trigger when the user says "log this receipt", "scan receipts", "new expense", "log this transaction", "add expense", "import venmo", "import bank csv", "create invoice", "run invoice scan", or mentions spend/income that needs tracking in the business Google Sheet. Uses python-scripts/invoice-system/main.py CLI. Use this even for a single transaction — consistent logging is the whole point.
---

# Invoice Expense Logger

Runs the Invoice & Tax Tracker workflow. Everything flows into the "Business Finance Tracker" Google Sheet.

**Sheet ID:** `1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw`
**Project:** `python-scripts/invoice-system/`
**Status:** LIVE on Mac

## Pick the right command

| User intent | Command |
|-------------|---------|
| Scan Gmail for new receipts | `scan-receipts` |
| Scan Gmail for new income/payments | `scan-payments` |
| Scan both at once (daily default) | `scan-all` |
| Manual entry (receipt didn't email) | `add-expense` |
| Import Venmo CSV | `import-csv --source venmo --file <path>` |
| Import bank CSV | `import-csv --source bank --file <path>` |
| Interactive invoice creation | `create-invoice` |
| First-time sheet setup | `setup-sheet` |

Stick to these 8 commands. They're documented in `main.py`'s docstring — don't invent new ones.

## Run pattern

```bash
cd python-scripts/invoice-system
python main.py <command> [flags]
```

**Common examples:**
```bash
python main.py scan-all
python main.py scan-receipts --days 60        # backfill 60 days
python main.py add-expense                    # interactive prompt
python main.py import-csv --source venmo --file ~/Downloads/venmo.csv
python main.py create-invoice
```

## What to verify after running

1. Terminal output shows rows written (e.g., "Added 3 transactions").
2. Open the sheet: https://docs.google.com/spreadsheets/d/1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw
3. Confirm expected rows in the right tab.

## Sheet tabs

Per `invoice-system.md`:
- **Transactions** — income from clients (and business expenses as negative values)
- **Invoices** — generated invoices
- **Invoice Line Items** — breakdown per invoice
- **Tax Summary** — auto-calculated totals

If Gray's memory mentions a "Business Expenses" tab and the actual sheet doesn't have one, trust the sheet. Flag the mismatch so memory gets updated.

## Common failure modes

| Symptom | Fix |
|---------|-----|
| 401 from Gmail or Sheets | Google OAuth expired — use the `google-oauth-refresh` skill |
| "No new emails found" on scan-receipts | Bump `--days`, or the Gmail filter missed them |
| Interactive command hangs on Windows | Encoding issue — confirm `main.py:36-38` still does the utf-8 reconfig |
| Receipt misclassified | The Claude classifier made a call — don't retry (costs money); manually edit the sheet row |

## Don't do this

- **Don't re-run scan-receipts or scan-payments "to test"** — each run costs Claude API calls on new emails. Ask Gray before re-running after a fix.
- **Don't edit the sheet manually, then re-run a scan** — dedup isn't perfect.
- **Don't add new CLI commands** without Gray asking. The 8 documented commands are the surface area.
- **Don't invent environment variables.** The `.env` keys are: `ANTHROPIC_API_KEY`, `GOOGLE_SHEET_ID`, `GMAIL_CREDENTIALS_PATH`.
