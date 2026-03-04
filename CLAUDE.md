# My Project — Claude Context

## Who I Am
Gray Davis. I'm building personal automation tools with Claude's help.

## Projects

### 1. AI Email Agent (`python-scripts/email-agent/`)
An automated Gmail assistant that runs hourly (7am–8pm).

**What it does:**
- Checks Gmail for new emails
- Classifies each email using Claude: `needs_reply`, `fyi_only`, or `ignore`
- Drafts replies in my writing style (trained on my sent emails via `voice_analyzer.py`)
- Sends drafts to my Slack DM with Send / Edit / Skip buttons
- Sends approved replies back through Gmail

**Key files:**
- `main.py` — orchestrates the whole flow
- `classifier.py` — Claude-powered email classification
- `drafter.py` — Claude-powered reply drafting
- `voice_analyzer.py` — analyzes my sent emails to build a writing style profile
- `gmail_client.py` — Gmail API (OAuth2, fetch, label, send)
- `slack_bot.py` — Slack Socket Mode bot with interactive buttons
- `config.py` — API keys, schedule, categories

**Stack:** Python, Claude (claude-sonnet-4-6), Gmail API, Slack SDK, python-dotenv, schedule

**Runs as:** macOS launch agent via `com.graydavis.emailagent.plist`

---

### 2. Invoice & Accounting System (`python-scripts/invoice-system/`)
A CLI tool for managing business finances.

**What it does:**
- Imports transactions from Venmo and bank CSV exports
- Scans Gmail for receipts and extracts data using Claude
- Generates professional PDF invoices and emails them to clients
- Tracks everything in Google Sheets with automatic tax/profit calculations

**Key files:**
- `main.py` — CLI with commands: `setup-sheet`, `import-csv`, `scan-receipts`, `create-invoice`
- `csv_importer.py` — parses Venmo and bank CSVs
- `receipt_scanner.py` — Gmail receipt extraction using Claude
- `invoice_generator.py` — PDF generation (ReportLab) + email sending
- `sheets_client.py` — Google Sheets API (tabs, formulas, invoice tracking)
- `gmail_client.py` — Gmail for fetching receipts and sending invoices

**Stack:** Python, Claude (claude-sonnet-4-6), Gmail API, Google Sheets API (gspread), ReportLab, python-dotenv

---

### Social Media Scraper (`python-scripts/social-media-analytics/`)
A YouTube analytics dashboard that pulls channel data and generates AI-powered insights.

**What it does:**
- Fetches all public videos from the authenticated YouTube channel
- Pulls analytics: views, watch time, avg view %, CTR, likes, comments, shares, subscribers gained
- Writes everything to a Google Sheet
- Sends data to Claude for deep analysis (top/bottom performers, retention, CTR, recommendations)
- Writes the AI analysis to an "AI Insights" tab in the sheet
- Runs daily via `run_daily.bat`

**Key files:**
- `main.py` — orchestrates fetch → sheets → AI analysis
- `youtube_fetcher.py` — YouTube Data API + Analytics API (OAuth2)
- `ai_analyzer.py` — Claude-powered channel analysis, writes to Google Sheets
- `comment_summarizer.py` — summarizes video comments
- `sheets_writer.py` — Google Sheets output
- `auth.py` — Google OAuth2 credentials

**Stack:** Python, Claude (claude-sonnet-4-6), YouTube Data API v3, YouTube Analytics API v2, Google Sheets API (gspread), python-dotenv

**Runs as:** Windows scheduled task via `run_daily.bat`

---

## Planned / Empty Folders
- `web-apps/` — future web projects
- `mobile-apps/` — future mobile projects
- `business/emails/`, `business/leads/`, `business/social-media/` — future business docs

## How to Run Each Project

### Email Agent
```bash
cd python-scripts/email-agent
python main.py          # starts the scheduled agent (runs hourly 7am–8pm)
```
- Runs as macOS launch agent via `com.graydavis.emailagent.plist`
- Requires: `.env` with keys below + `credentials.json` + `token.json`

### Invoice System
```bash
cd python-scripts/invoice-system
python main.py setup-sheet      # create/configure Google Sheet tabs
python main.py import-csv       # import Venmo or bank CSV
python main.py scan-receipts    # scan Gmail for receipts
python main.py create-invoice   # generate and email a PDF invoice
```
- Invoices saved to `~/Desktop/Invoices/`
- Requires: `.env` with keys below + `credentials.json` + `token.json`

### Social Media Scraper
```bash
cd python-scripts/social-media-analytics
python main.py          # fetch YouTube data → Sheets → AI analysis
# or double-click run_daily.bat on Windows
```
- Requires: `.env` with keys below + `client_secret.json` + `token.json`

---

## Environment Variables (names only — values are in each project's `.env`)

### Email Agent (`python-scripts/email-agent/.env`)
- `ANTHROPIC_API_KEY` — Claude API key
- `SLACK_BOT_TOKEN` — Slack bot token (xoxb-...)
- `SLACK_APP_TOKEN` — Slack app-level token (xapp-...)
- `SLACK_USER_ID` — Your Slack user ID (for DMs)
- `GMAIL_CREDENTIALS_PATH` — path to credentials.json (default: credentials.json)

### Invoice System (`python-scripts/invoice-system/.env`)
- `ANTHROPIC_API_KEY` — Claude API key
- `GOOGLE_SHEET_ID` — ID of your finance Google Sheet
- `GMAIL_CREDENTIALS_PATH` — path to credentials.json (default: credentials.json)

### Social Media Scraper (`python-scripts/social-media-analytics/.env`)
- `ANTHROPIC_API_KEY` — Claude API key
- `SHEET_ID` — auto-filled on first run
- `NOTION_TOKEN` — (optional) Notion integration token
- `NOTION_PAGE_ID` — (optional) parent Notion page for weekly reports

---

## Security Notes
- All `.env`, `token.json`, `client_secret.json`, `credentials.json` are in `.gitignore` — never committed
- OAuth tokens auto-refresh; if auth breaks, delete `token.json` and re-run to re-authenticate
- API keys live only in `.env` files — never hardcoded in source

---

## Setup
- Repo is synced via GitHub: `https://github.com/graydavis33/my-project`
- Auto-syncs on login (Windows Task Scheduler + Mac cron job)
- Both Mac and Windows are set up

## Preferences
- Language: Python
- AI model: claude-sonnet-4-6
- Keep things simple and practical

## Efficiency & Token Optimization
When building or modifying any feature that calls Claude:
- **Minimize Claude calls** — only invoke Claude when no simpler/cheaper solution exists (regex, string matching, caching, etc.)
- **Cache aggressively** — cache Claude outputs (voice profiles, classifications, analyses) to disk so repeated runs don't re-call the API
- **Batch where possible** — send multiple items in one prompt instead of one call per item
- **Trim prompts** — keep system prompts and context tight; avoid redundant instructions or padding
- **Use cheaper models for simple tasks** — if a task is classification or extraction with low complexity, prefer haiku-class models where appropriate
- **Skip Claude entirely when possible** — if logic can be handled with code (keyword matching, rules, conditionals), do it in code
- **Short-circuit early** — filter out irrelevant data (e.g. `ignore`-class emails, already-processed items) before sending anything to Claude
