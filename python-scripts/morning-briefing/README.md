# Daily Morning Briefing

## What It Does
- Sends one Slack DM at 8am with a full-day briefing
- Emails needing reply (reads `pending_drafts.json` from Email Agent — no API call)
- Outstanding invoices (reads Invoice Google Sheet)
- Top social media performer this week (reads Analytics Google Sheet)
- Top 3 priorities for the day (editable list in `config.py`)

## Key Files
- `main.py` — entry point, scheduler
- `briefing.py` — assembles and sends briefing
- `gmail_summary.py` — reads pending_drafts.json
- `sheets_summary.py` — reads Invoice + Analytics sheets
- `config.py` — daily priorities list, API keys

## Stack
Python, Slack SDK, Gmail API, Google Sheets (gspread), python-dotenv, schedule

## Run
```bash
cd python-scripts/morning-briefing
python main.py            # test run
python main.py --schedule # run at 8am daily
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_USER_ID`, `INVOICE_SHEET_ID`, `ANALYTICS_SHEET_ID`, `EMAIL_AGENT_DIR`, `GOOGLE_CREDENTIALS_PATH`

## Status
Built on Windows. Needs `.env` setup to run on Mac.
