# Workflow: Invoice System

**Status:** LIVE on Mac
**Cost:** Minimal — Claude Sonnet for receipt scanning
**Script:** `python-scripts/invoice-system/`
**Sheet:** https://docs.google.com/spreadsheets/d/1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw

---

## Objective

Track all income and expenses, scan Gmail for receipts, generate and email professional PDF invoices, and maintain a clean Google Sheet for tax time.

---

## Commands

```bash
cd python-scripts/invoice-system

# Setup (run once)
python main.py setup-sheet

# CSV imports
python main.py import-csv --file X --source venmo
python main.py import-csv --file X --source bank

# Gmail scans
python main.py scan-receipts                     # expense receipts → Business Expenses, default 30d
python main.py scan-receipts --days 7
python main.py scan-payments                     # income payments → Transactions, default 30d
python main.py scan-payments --days 90
python main.py scan-all                          # runs both scan-receipts + scan-payments once
python main.py scan-all --schedule               # daemon mode — runs daily at 08:00 (override with --time HH:MM)
python main.py scan-all --schedule --time 09:00  # VPS runs this at 9am via cron

# Manual entry
python main.py add-expense                       # interactive prompt: date, vendor, category, amount, notes
python main.py create-invoice                    # pick template → fill details → PDF + email
```

Note: the email-agent automatically fires `scan-payments --days 2` after every hourly email check. So if email-agent is running on the VPS, you rarely need to call `scan-payments` manually.

---

## Sheet Structure

Sheet name: **Business Finance Tracker**

| Tab | What's In It |
|-----|-------------|
| Transactions | Date, Payer, Source, Amount ($), Notes |
| Business Expenses | Date, Vendor, Category (9 options), Amount ($), Notes |
| Invoices | Invoice-level metadata |
| Invoice Line Items | Per-line-item breakdown for each invoice |
| Tax Summary | Auto-calculated totals |

The 9 expense categories (defined in `config.py → CATEGORIES`): Groceries, Dining Out, Software & Tools, Streaming, Utilities, Transport, Health & Wellness, Shopping, Misc.

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| Sheet auth error | OAuth token expired — re-run auth flow. Check `GMAIL_CREDENTIALS_PATH` in `.env` |
| CSV import fails | Verify the file is a real Venmo or bank CSV export — format matters |
| Invoice template wrong | Edit rates in `invoice_templates.json` before generating |
| Receipt not found | Gmail scans batches of 5 — run again or increase `--days` range |

---

## Env Vars Required

```
ANTHROPIC_API_KEY
GOOGLE_SHEET_ID=1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw
GMAIL_CREDENTIALS_PATH
```

---

## Notes

- Invoices save to `~/Desktop/Invoices/`
- Fill in rates in `invoice_templates.json` before first invoice
- VPS runs `scan-all` daily at 9am via cron (set by `deploy/vps-setup.sh`)
- Payment scanner also fires from the email-agent loop every hour — double-coverage is intentional
