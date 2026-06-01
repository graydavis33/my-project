# Email Agent

## What It Does
- Checks Gmail every hour (7am–8pm), classifies emails as `needs_reply`, `fyi_only`, or `ignore`
- Drafts replies in Gray's voice, sends to Slack DM with Send / Edit / Skip buttons
- Applies Gmail labels automatically per category
- Voice profile auto-refreshes every 30 days from sent emails

## Key Files
- `main.py` — orchestration, logging setup
- `classifier.py` — Claude email classification
- `drafter.py` — Claude reply drafting (uses voice_profile.txt)
- `voice_analyzer.py` — builds/refreshes writing style profile
- `gmail_client.py` — Gmail API (OAuth2, fetch, label, send)
- `slack_bot.py` — Slack Socket Mode bot, interactive buttons, tracks stats in `draft_stats.json`
- `config.py` — API keys, schedule, categories

## Stack
Python, Claude (claude-sonnet-4-6), Gmail API, Slack SDK, python-dotenv, schedule

## Run
```bash
cd python-scripts/email-agent && python main.py
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_USER_ID`, `GMAIL_CREDENTIALS_PATH`

## Status
LIVE on Mac. Runs hourly via macOS launchd. Voice profile built from 24 sent emails.

## Notes
- Gmail label `agent-processed` prevents duplicate processing
- Labels: Agent/Needs Reply, Agent/FYI Only, Agent/Ignore
- Windows: `run_agent.bat` + `install_windows_task.ps1` for Task Scheduler
- TODO: Calibrate tone further with email screenshots Gray will provide
