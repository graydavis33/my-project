# Client CRM + Pipeline Tracker

## What It Does
- Tracks clients through stages: Lead → Pitched → Contracted → In Production → Delivered → Paid
- CLI: add, list, update, remind
- Google Sheets: Clients tab + Pipeline Summary (auto-created on setup)
- Monday 9am Slack reminder for overdue follow-ups + unpaid invoices

## Key Files
- `main.py` — CLI entry: `setup`, `add`, `list [--stage X]`, `update <id> <stage>`, `remind`
- `crm_sheets.py` — Google Sheets read/write
- `reminder.py` — stage-based reminder logic
- `slack_notifier.py` — Slack DM
- `config.py` — reminder thresholds per stage

## Stack
Python, Google Sheets (gspread), Slack SDK, python-dotenv, schedule

## Run
```bash
cd python-scripts/client-crm
python main.py setup   # first time — creates Google Sheet
python main.py add / list / update / remind / --schedule
```

## Env Vars (.env)
`SLACK_BOT_TOKEN`, `SLACK_USER_ID`, `GOOGLE_CREDENTIALS_PATH`, `CRM_SHEET_ID` (auto-filled after setup)

## Status
Built on Windows. Run `python main.py setup` first to create the Google Sheet.
