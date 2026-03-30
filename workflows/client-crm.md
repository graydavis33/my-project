# Workflow: Client CRM

**Status:** Built on Windows — needs `python main.py setup` to initialize
**Cost:** Free — no AI calls, just Sheets + Slack
**Script:** `python-scripts/client-crm/`

---

## Objective

Track every client through the full sales and production pipeline. Get Monday morning Slack reminders for anyone overdue for follow-up.

---

## Pipeline Stages

`Lead → Pitched → Contracted → In Production → Delivered → Paid`

---

## Commands

```bash
cd python-scripts/client-crm

python main.py setup                    # First time only — creates Google Sheet
python main.py add                      # Add a new client (interactive)
python main.py list                     # List all clients
python main.py list --stage Pitched     # Filter by stage
python main.py update <id> Contracted   # Move client to new stage
python main.py remind                   # Manual reminder check
python main.py --schedule               # Run with Monday reminder scheduler
```

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| Setup fails | Check `GOOGLE_CREDENTIALS_PATH` in `.env` — needs Google OAuth credentials |
| Slack reminders not arriving | Check `SLACK_BOT_TOKEN` and `SLACK_USER_ID` in `.env` |
| `CRM_SHEET_ID` missing | Run `setup` first — it auto-fills this in `.env` after creating the sheet |

---

## Env Vars Required

```
SLACK_BOT_TOKEN
SLACK_USER_ID
GOOGLE_CREDENTIALS_PATH
CRM_SHEET_ID   # auto-filled after running setup
```

---

## Setup Checklist (First Run)

- [ ] `.env` filled with Slack + Google credentials
- [ ] Run `python main.py setup` — creates Google Sheet + fills `CRM_SHEET_ID`
- [ ] Add first client with `python main.py add`
- [ ] Run `python main.py --schedule` to keep Monday reminders active
