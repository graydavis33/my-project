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

python main.py setup-sheet              # First time only — creates Sheet tabs + headers
python main.py import-csv --file X --source venmo   # Import Venmo transactions
python main.py import-csv --file X --source bank    # Import bank CSV
python main.py scan-receipts            # Scan Gmail for receipts (last 30 days default)
python main.py scan-receipts --days 7   # Scan last 7 days only
python main.py create-invoice           # Interactive: pick template → fill details → PDF + email
```

---

## Sheet Structure

| Tab | What's In It |
|-----|-------------|
| Transactions | Date, Payer, Source, Amount ($), Notes |
| Business Expenses | Date, Vendor, Category, Amount ($), Notes |
| Tax Summary | Auto-calculated totals |

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
- TODO: Schedule `scan-receipts` to run daily automatically
