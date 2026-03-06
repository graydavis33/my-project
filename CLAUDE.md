# My Project — Claude Context

## Who I Am
Gray Davis. I'm building personal automation tools with Claude's help.

**Background:**
- Freelance videographer — films and edits for clients
- Spent 9 months at a marketing agency filming/editing for clients' social media
- Pursuing role as personal videographer for a young CEO
- Creating own content: videography tips, editing, AI tools, camera/gear, Claude coding

**Goals:**
- Become a well-versed AI operator/manager
- Automate and optimize business, videography, editing, and personal life
- Create tools to eventually monetize and sell as products
- Grow on social media, stay ahead of the AI curve

---

## Projects

### 1. AI Email Agent (`python-scripts/email-agent/`)
An automated Gmail assistant that runs hourly (7am–8pm).

**What it does:**
- Checks Gmail for new emails
- Classifies each email using Claude: `needs_reply`, `fyi_only`, or `ignore`
- Drafts replies in my writing style (voice profile auto-refreshes every 30 days)
- Sends drafts to my Slack DM with Send / Edit / Skip buttons
- Sends approved replies back through Gmail
- Structured logging → `agent.log` (file + console)
- Draft action stats tracked → `draft_stats.json` (sent/skipped/edited counts)

**Key files:**
- `main.py` — orchestrates the whole flow, logging setup
- `classifier.py` — Claude-powered email classification
- `drafter.py` — Claude-powered reply drafting
- `voice_analyzer.py` — builds writing style profile; `voice_profile_needs_refresh()` checks 30-day staleness
- `gmail_client.py` — Gmail API (OAuth2, fetch, label, send)
- `slack_bot.py` — Slack Socket Mode bot with interactive buttons; tracks stats via `_update_stats()`
- `config.py` — API keys, schedule, categories

**Stack:** Python, Claude (claude-sonnet-4-6), Gmail API, Slack SDK, python-dotenv, schedule

---

### 2. Invoice & Accounting System (`python-scripts/invoice-system/`)
A CLI tool for managing business finances.

**What it does:**
- Imports transactions from Venmo and bank CSV exports
- Scans Gmail for receipts (batch processing: 5 emails/call, ~35% token savings)
- 12 receipt keyword types — catches charges, renewals, statements, and more
- Invoice templates (5 service types in `invoice_templates.json`) — select at creation time; rates set to 0, fill in once
- Generates professional PDF invoices and emails them to clients
- Tracks everything in Google Sheets with automatic tax/profit calculations

**Key files:**
- `main.py` — CLI: `setup-sheet`, `import-csv`, `scan-receipts`, `create-invoice`
- `csv_importer.py` — parses Venmo and bank CSVs
- `receipt_scanner.py` — batch Gmail receipt extraction; falls back to individual on parse error
- `invoice_generator.py` — PDF generation (ReportLab) + email; shows template menu at creation
- `invoice_templates.json` — 5 service templates (fill in rates before first use)
- `sheets_client.py` — Google Sheets API
- `gmail_client.py` — Gmail for receipts and sending invoices

**Stack:** Python, Claude (claude-sonnet-4-6), Gmail API, Google Sheets API (gspread), ReportLab, python-dotenv

---

### 3. Social Media Analytics (`python-scripts/social-media-analytics/`)
Multi-platform analytics dashboard: YouTube (live), TikTok/Instagram/Facebook (blocked on API setup).

**What it does:**
- Fetches videos/posts from all configured platforms
- Pulls analytics: views, likes, comments, shares, watch time, CTR, engagement rate, etc.
- Writes to Google Sheets (one tab per platform + shared tabs)
- AI insights via Claude Haiku (cached daily); optional deep Sonnet analysis → Notion
- Runs weekly via GitHub Actions (every Sunday 9 AM EST)

**Key files:**
- `main.py` — orchestrates fetch → AI insights → Sheets → Notion
- `youtube_fetcher.py` — YouTube Data API v3 + Analytics API v2 (Google OAuth2)
- `meta_fetcher.py` — Instagram + Facebook via Meta Graph API v19.0
- `tiktok_fetcher.py` — TikTok Display API with cursor pagination + auto token refresh
- `tiktok_auth.py` — one-time TikTok OAuth2 browser flow
- `ai_analyzer.py` — Claude analysis (Haiku cached + Sonnet → Notion)
- `comment_summarizer.py` — on-demand comment summarizer (run separately)
- `sheets_writer.py` — platform-agnostic Google Sheets output
- `.github/workflows/social-media-analytics.yml` — GitHub Actions weekly schedule

**Multi-platform architecture:**
- Each video dict has a `platform` field: `'YouTube'`, `'TikTok'`, `'Instagram'`, `'Facebook'`
- Missing env vars = that platform is silently skipped (no crash)
- To add a new platform: write a new fetcher, call it in `main.py` with the same guard pattern

**Google Sheets tabs:** Dashboard, YouTube Shorts, YouTube Longform, TikTok, Instagram, Facebook, Comments, Best Posting Day, Title Analysis

**Token management:**
- YouTube: Google OAuth2 token auto-refreshes (token.json)
- Meta: 60-day long-lived token in .env — refresh manually every 60 days
- TikTok: access token (~24h) auto-refreshes on 401; refresh token lasts 365 days (tiktok_token.json)

**Stack:** Python, Claude (claude-haiku-4-5 for Sheets, claude-sonnet-4-6 for Notion), YouTube Data API v3, YouTube Analytics API v2, Meta Graph API v19.0, TikTok Display API, gspread, requests, python-dotenv

---

### 4. Hook + Title Optimizer (`python-scripts/hook-optimizer/`)
CLI: input a video concept → Claude outputs 5 YouTube titles, 5 TikTok titles, 3 hooks, thumbnail concept, best bet pick.

**Key features:**
- Concept cache (MD5 hash, 7-day TTL) — repeat concepts are instant, no API call
- Auto-saves every result to `results/{slug}-{timestamp}.txt`

**Run:** `python main.py "your video concept"`

---

### 5. Content Researcher (`python-scripts/content-researcher/`)
On-demand outlier video research tool. Type a concept → full research report with hooks, script, and performance analysis written to Notion.

**What it does:**
- Generates 4 YouTube search query variants from your concept (Claude Haiku)
- Searches YouTube, collects ~60 videos, fetches subscriber counts
- Ranks by views-to-subscriber ratio (surfaces hidden viral gems, not just big channels)
- Pulls first 90s transcripts from top 10 outliers (hook extraction)
- One Claude Sonnet call generates a 9-section report: performance data, outlier reasons, top 5 hook patterns, format/length recs, keywords, 5 mini hooks, script outline, full script draft, pacing & sound design notes
- Writes report to a new Notion page + saves local `.md` file in `results/`
- Caches results for 7 days — same concept = instant re-run, $0 cost

**Key files:** `main.py`, `searcher.py`, `outlier.py`, `transcript.py`, `analyzer.py`, `notion_writer.py`, `cache.py`

**Stack:** Python, Claude (claude-haiku-4-5 for query gen, claude-sonnet-4-6 for analysis), YouTube Data API v3, youtube-transcript-api, Notion API, python-dotenv

**Cost per run:** ~$0.04–0.06. Same concept within 7 days = $0.

**OAuth:** Shares `client_secret.json` from `../social-media-analytics/`. First run opens browser for YouTube auth (saves `token.json` locally).

**V2 roadmap:** Reddit research layer, TikTok (when developer setup done), Google Trends

---

### 6. Daily Morning Briefing (`python-scripts/morning-briefing/`)
Sends one Slack DM at 8am with a full-day briefing.

**What it does:**
- Emails needing reply (reads `pending_drafts.json` from Email Agent — no API call)
- Outstanding invoices (reads Invoice Google Sheet)
- Top social media performer this week (reads Analytics Google Sheet)
- Top 3 priorities for the day (editable list in `config.py`)

**Key files:** `main.py`, `briefing.py`, `gmail_summary.py`, `sheets_summary.py`, `config.py`, `run_briefing.bat`

**Status:** Built. Needs `.env` setup before first run.

---

### 7. Client Onboarding Automation (`python-scripts/client-onboarding/`)
CLI: collect client info → Claude project brief → contract PDF → email → Sheets → Slack.

**What it does:**
- CLI intake: name, email, company, project type, scope, timeline, budget
- Claude generates a project brief from inputs
- Auto-generates contract PDF (ReportLab) and emails to client with brief attached
- Logs to Google Sheets client tracker (auto-creates sheet on first run, saves ID to .env)
- Slack DM: "New client onboarded: [Name]"

**Key files:** `main.py`, `intake.py`, `brief_generator.py`, `contract_template.py`, `contract_generator.py`, `onboarding_emailer.py`, `sheets_tracker.py`, `slack_notifier.py`

**Status:** Built. Review `contract_template.py` (update terms/rates) and add `.env` values before first real use.

---

### 8. Client CRM + Pipeline Tracker (`python-scripts/client-crm/`)
Google Sheets-backed client pipeline with CLI and Monday Slack reminders.

**What it does:**
- Tracks clients: Lead → Pitched → Contracted → In Production → Delivered → Paid
- CLI: `add`, `list [--stage X]`, `update <id> <stage>`, `remind`
- Google Sheets: Clients tab + Pipeline Summary with COUNTIF/SUMIF formulas (auto-created on setup)
- Monday 9am Slack reminder for overdue follow-ups + unpaid invoices
- Stage-based reminder thresholds (e.g. Lead→Pitched: 3 days, Pitched→Contracted: 7 days)

**Key files:** `main.py`, `crm_sheets.py`, `reminder.py`, `slack_notifier.py`, `config.py`, `install_windows_task.ps1`

**Status:** Built. Run `python main.py setup` first to create the Google Sheet.

---

### 9. Niche Creator Intelligence (`python-scripts/creator-intel/`)
Monitors 12 YouTube creators weekly → Claude pattern analysis → Monday Slack report.

**What it does:**
- Fetches last 10 videos per creator via YouTube Data API (reuses social-media-analytics credentials)
- One batched Claude call: trending formats, hook styles, best posting days, topic ideas, one immediate action
- Monday 9:30am Slack report
- 6-day cache — won't re-fetch if run within the week
- `creators.json` — pre-loaded with 12 creators (McKinnon, Haapoja, Kolder, MKBHD, D'Avella, etc.)

**Key files:** `main.py`, `youtube_fetcher.py`, `analyzer.py`, `slack_reporter.py`, `creators.json`, `config.py`

**Status:** Built. Needs `.env` setup. Reuses `social-media-analytics/client_secret.json` — no new credentials needed.

---

### 10. Content Repurposing Pipeline (`python-scripts/content-pipeline/`)
Input a video file → transcribe → Claude picks best clips → captions → optional ffmpeg cuts.

**What it does:**
- Transcribes via OpenAI Whisper API (optional — falls back to manual transcript paste if no key)
- Claude identifies 3–5 best short-form clip moments with timestamps + reasoning
- Writes platform-specific captions: TikTok, Instagram Reels, YouTube Shorts
- Optional ffmpeg auto-cut — skips gracefully if not installed
- Saves cut list + all captions to `output/{video}-results-{timestamp}.txt`

**Key files:** `main.py`, `transcriber.py`, `moment_picker.py`, `caption_writer.py`, `video_cutter.py`, `config.py`

**Run:** `python main.py path/to/video.mp4 [--no-cut] [--context "description"]`

**Status:** Built. Add `ANTHROPIC_API_KEY` to `.env`. Optional: add `OPENAI_API_KEY` for auto-transcription.

---

## Current Work in Progress — Multi-Platform Analytics Setup

**Status (paused 2026-03-05):** All code written and pushed. Blocked on user completing API developer account setup.

### TikTok — In Progress (paused mid-form):
1. For ToS + Privacy Policy URLs: try `https://www.tiktok.com/@[username]` (own profile URL)
2. For Web/Desktop URL: click "Verify URL properties" — or use TikTok profile URL for all three fields
3. Do NOT fill out App Review description or upload demo video — skip entirely
4. Look for "Save" / "Create App" (NOT "Submit for Review")
5. After app created: add Login Kit product, set redirect URI to `http://localhost:8888/callback`
6. Add own TikTok account as sandbox/test user
7. Add `TIKTOK_CLIENT_KEY` + `TIKTOK_CLIENT_SECRET` to `python-scripts/social-media-analytics/.env`
8. Run once: `python tiktok_auth.py`

### Instagram + Facebook — Not yet started:
1. Create Meta Developer App at developers.facebook.com
2. Add products: Instagram Graph API + Facebook Login for Business
3. Get long-lived token from Graph API Explorer with: `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement`, `pages_show_list`, `read_insights`
4. Exchange for 60-day token via `GET /oauth/access_token?grant_type=fb_exchange_token&...`
5. Get `FACEBOOK_PAGE_ID` via `GET /me/accounts`
6. Get `INSTAGRAM_BUSINESS_ACCOUNT_ID` via `GET /{PAGE_ID}?fields=instagram_business_account`
7. Add all three to `.env`: `META_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `FACEBOOK_PAGE_ID`

---

## Planned / Empty Folders
- `web-apps/` — future web projects
- `mobile-apps/` — future mobile projects
- `business/emails/`, `business/leads/`, `business/social-media/` — future business docs

---

## How to Run Each Project

```bash
# Email Agent
cd python-scripts/email-agent && python main.py

# Invoice System
cd python-scripts/invoice-system && python main.py [setup-sheet|import-csv|scan-receipts|create-invoice]

# Social Media Analytics
cd python-scripts/social-media-analytics && python main.py

# Hook + Title Optimizer
cd python-scripts/hook-optimizer && python main.py "your concept"

# Content Researcher
cd python-scripts/content-researcher && python main.py "your video concept"

# Daily Morning Briefing
cd python-scripts/morning-briefing && python main.py [--schedule]

# Client Onboarding
cd python-scripts/client-onboarding && python main.py

# Client CRM
cd python-scripts/client-crm && python main.py setup        # first time
cd python-scripts/client-crm && python main.py [add|list|update|remind|--schedule]

# Creator Intel
cd python-scripts/creator-intel && python main.py [--schedule]

# Content Pipeline
cd python-scripts/content-pipeline && python main.py path/to/video.mp4 [--no-cut] [--context "..."]
```

---

## Environment Variables (names only — values in each project's `.env`)

### Email Agent
- `ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_USER_ID`, `GMAIL_CREDENTIALS_PATH`

### Invoice System
- `ANTHROPIC_API_KEY`, `GOOGLE_SHEET_ID`, `GMAIL_CREDENTIALS_PATH`

### Social Media Analytics
- `ANTHROPIC_API_KEY`, `SHEET_ID` (auto-filled), `NOTION_TOKEN` (optional), `NOTION_PAGE_ID` (optional)
- `META_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `FACEBOOK_PAGE_ID`
- `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`

### Hook + Title Optimizer
- `ANTHROPIC_API_KEY`

### Content Researcher
- `ANTHROPIC_API_KEY`, `NOTION_TOKEN` (optional), `NOTION_PAGE_ID` (optional)

### Daily Morning Briefing
- `ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_USER_ID`
- `INVOICE_SHEET_ID`, `ANALYTICS_SHEET_ID`, `EMAIL_AGENT_DIR`, `GOOGLE_CREDENTIALS_PATH`

### Client Onboarding
- `ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_USER_ID`
- `GMAIL_CREDENTIALS_PATH`, `ONBOARDING_SHEET_ID` (auto-filled), `YOUR_NAME`, `YOUR_EMAIL`, `YOUR_TITLE`

### Client CRM
- `SLACK_BOT_TOKEN`, `SLACK_USER_ID`, `GOOGLE_CREDENTIALS_PATH`, `CRM_SHEET_ID` (auto-filled)

### Creator Intel
- `ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_USER_ID`
- `YOUTUBE_CREDENTIALS_PATH` (defaults to `../social-media-analytics/client_secret.json`)

### Content Pipeline
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (optional — for Whisper auto-transcription)

---

## Security Notes
- All `.env`, `token.json`, `client_secret*.json`, `credentials.json` are in `.gitignore` — never committed
- OAuth tokens auto-refresh; if auth breaks, delete `token.json` and re-run
- API keys live only in `.env` files — never hardcoded in source

---

## Setup
- Repo: `https://github.com/graydavis33/my-project`
- Dashboard: `https://graydavis33.github.io/my-project/dashboard.html`
- Auto-syncs on login (Windows Task Scheduler + Mac cron job)
- Both Mac and Windows are set up

---

## Preferences
- Language: Python only
- AI model: claude-sonnet-4-6
- Keep things simple and practical
- User wants to be taught as we build — use strong bullet points
- Don't over-engineer; build simple things first

---

## Efficiency & Token Optimization
When building or modifying any feature that calls Claude:
- **Minimize Claude calls** — only invoke Claude when no simpler/cheaper solution exists
- **Cache aggressively** — cache outputs to disk so repeated runs don't re-call the API
- **Batch where possible** — send multiple items in one prompt instead of one call per item
- **Trim prompts** — keep system prompts tight; avoid redundant instructions or padding
- **Use cheaper models for simple tasks** — prefer haiku-class for classification/extraction
- **Skip Claude entirely when possible** — keyword matching, rules, conditionals first
- **Short-circuit early** — filter irrelevant data before sending anything to Claude
