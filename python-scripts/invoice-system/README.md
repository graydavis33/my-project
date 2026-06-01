# Invoice & Tax Tracker

## What It Does
- Imports transactions from Venmo and bank CSV exports
- Scans Gmail for receipts (batches of 5 emails/call)
- Generates professional PDF invoices, emails to clients
- Tracks everything in Google Sheets with automatic tax/profit calculations

## Key Files
- `main.py` — CLI entry: `setup-sheet`, `import-csv`, `scan-receipts`, `create-invoice`
- `csv_importer.py` — parses Venmo and bank CSVs; Zelle auto-detected from descriptions
- `receipt_scanner.py` — batch Gmail receipt extraction
- `invoice_generator.py` — PDF generation (ReportLab) + email; shows template menu
- `invoice_templates.json` — 5 service templates (fill in rates before first use)
- `sheets_client.py` — Google Sheets API (gspread)
- `gmail_client.py` — Gmail for receipts and sending invoices

## Stack
Python, Claude (claude-sonnet-4-6), Gmail API, Google Sheets API (gspread), ReportLab, python-dotenv

## Run
```bash
cd python-scripts/invoice-system
python main.py setup-sheet        # first time only
python main.py import-csv --file X --source venmo/bank
python main.py scan-receipts [--days N]
python main.py create-invoice
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `GOOGLE_SHEET_ID`, `GMAIL_CREDENTIALS_PATH`

## Status
LIVE on Mac. Google Sheet ID: `1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw`
Sheet name: "Business Finance Tracker" — tabs: Transactions | Invoices | Invoice Line Items | Tax Summary

## Notes
- Invoices saved to `~/Desktop/Invoices/`
- TODO: Schedule `scan-receipts` to run automatically daily
