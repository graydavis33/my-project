# Client Onboarding Automation

## What It Does
- CLI intake: name, email, company, project type, scope, timeline, budget
- Claude generates a project brief from inputs
- Auto-generates contract PDF (ReportLab), emails to client with brief attached
- Logs to Google Sheets client tracker
- Slack DM: "New client onboarded: [Name]"

## Key Files
- `main.py` — CLI entry
- `intake.py` — collects client info interactively
- `brief_generator.py` — Claude generates project brief
- `contract_template.py` — **update terms/rates here before first real use**
- `contract_generator.py` — builds PDF contract
- `onboarding_emailer.py` — sends email with contract + brief
- `sheets_tracker.py` — logs to Google Sheets (auto-creates sheet on first run)
- `slack_notifier.py` — Slack DM notification

## Stack
Python, Claude (claude-sonnet-4-6), Gmail API, Google Sheets (gspread), ReportLab, Slack SDK

## Run
```bash
cd python-scripts/client-onboarding && python main.py
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_USER_ID`, `GMAIL_CREDENTIALS_PATH`, `ONBOARDING_SHEET_ID`, `YOUR_NAME`, `YOUR_EMAIL`, `YOUR_TITLE`

## Status
Built on Windows. Review `contract_template.py` and add `.env` values before first real use.
