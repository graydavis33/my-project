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
A multi-platform analytics dashboard supporting YouTube, TikTok, Instagram, and Facebook.

**What it does:**
- Fetches videos/posts from all configured platforms
- Pulls analytics: views, likes, comments, shares, watch time, CTR, engagement rate, etc.
- Computes derived metrics: engagement rate, views gained since last run, growth %
- Writes to Google Sheets (one tab per platform + shared tabs)
- Generates AI insights via Claude Haiku (dashboard summary + title patterns, batched, cached daily)
- Optionally writes deep Sonnet analysis to Notion (if NOTION_TOKEN configured)
- Runs weekly via GitHub Actions (every Sunday 9 AM EST) — also triggerable manually

**Key files:**
- `main.py` — orchestrates fetch (all platforms) → AI insights → Sheets → Notion
- `youtube_fetcher.py` — YouTube Data API v3 + Analytics API v2 (Google OAuth2)
- `meta_fetcher.py` — Instagram + Facebook via Meta Graph API v19.0 (static token in .env)
- `tiktok_fetcher.py` — TikTok Display API (token from tiktok_token.json)
- `tiktok_auth.py` — one-time TikTok OAuth2 browser flow; run once to set up
- `ai_analyzer.py` — Claude-powered analysis: `get_sheet_insights()` (Haiku, cached) + `analyze_and_write()` (Sonnet → Notion)
- `comment_summarizer.py` — on-demand comment summarizer (run separately)
- `sheets_writer.py` — Google Sheets output; `write_video_data(videos, ai_insights)` is platform-agnostic
- `auth.py` — Google OAuth2 credentials
- `.github/workflows/social-media-analytics.yml` — GitHub Actions weekly schedule

**Multi-platform architecture:**
- Each video dict has a `platform` field: `'YouTube'`, `'TikTok'`, `'Instagram'`, `'Facebook'`
- `write_video_data()` handles all platforms; platform-specific tabs filter by `platform` field
- Missing env vars = that platform is silently skipped (no crash)
- To add a new platform: write a new fetcher, call it in `main.py` with the same guard pattern

**Google Sheets tabs:**
- `Dashboard` — channel overview per platform + top/bottom 5 videos + AI summary
- `YouTube Shorts` — per-video metrics for YouTube Shorts
- `YouTube Longform` — per-video metrics for YouTube long-form videos
- `TikTok` — per-video metrics (views, likes, comments, shares; no watch time/CTR via API)
- `Instagram` — per-post metrics (views, reach, likes, comments, shares, saves)
- `Facebook` — per-post metrics (impressions, likes, comments, shares, video views)
- `Comments` — comment counts + AI summaries (via comment_summarizer.py)
- `Best Posting Day` — avg performance by day of week per platform
- `Title Analysis` — word frequency for top vs bottom performers + AI title insights

**Stack:** Python, Claude (claude-haiku-4-5 for Sheets insights, claude-sonnet-4-6 for Notion), YouTube Data API v3, YouTube Analytics API v2, Meta Graph API v19.0, TikTok Display API, Google Sheets API (gspread), requests, python-dotenv

**Runs as:** GitHub Actions weekly (Sunday 9 AM EST)

**Token management:**
- YouTube: Google OAuth2 token auto-refreshes (token.json)
- Meta (Instagram + Facebook): 60-day long-lived token in .env — refresh manually every 60 days
- TikTok: access token (~24h) auto-refreshes on 401; refresh token lasts 365 days (tiktok_token.json)

---

## Current Work in Progress — Multi-Platform Analytics Setup

**Status (paused 2026-03-05):** All code is written and committed. User is mid-way through TikTok
developer app creation and hit a form blocker on the URL validation.

### What's done (code complete, committed, pushed):
- `meta_fetcher.py` — Instagram + Facebook via Meta Graph API
- `tiktok_fetcher.py` — TikTok Display API with cursor pagination + auto token refresh
- `tiktok_auth.py` — one-time PKCE OAuth2 browser flow for TikTok
- `sheets_writer.py` — TikTok, Instagram, Facebook tabs + platform-specific headers
- `main.py` — fetches all 4 platforms, silently skips any not configured
- `requirements.txt` — added `requests>=2.31.0`

### TikTok — In Progress (paused mid-form):
User signed in at developers.tiktok.com, created a developer account (Individual), and reached
the app creation form. Filled in app name/description/platform (Web). Hit URL validation errors:

**Known issues with the form:**
- Terms of Service URL + Privacy Policy URL: form shows "Enter a valid URL beginning with https://"
  even though URLs do start with https:// — TikTok may be doing live URL verification or requiring
  a domain they can validate. Tried: GitHub repo root, GitHub Pages URL — both failed.
- Web/Desktop URL: shows "This URL is not verified. Verify URL properties" — TikTok requires
  domain ownership verification for this field.
- App Review section requires a description text + demo video upload — but this is only needed
  for PUBLIC app submission, NOT for sandbox/test user access.

**Next session — pick up here:**
1. For ToS + Privacy Policy URLs: try using `https://www.tiktok.com/@[username]` (user's own profile)
   or any other live HTTPS URL that passes TikTok's validator
2. For Web/Desktop URL: click "Verify URL properties" — TikTok will give instructions to add a
   DNS TXT record or meta tag to the domain. Since we don't own a custom domain, the simplest
   workaround is to use their TikTok profile URL for all three URL fields.
3. Do NOT fill out the App Review description or upload a demo video — skip those fields entirely
4. Look for "Save" / "Create App" button (NOT "Submit for Review") at bottom of form
5. After app created: add Login Kit product, set redirect URI to `http://localhost:8888/callback`
6. Add own TikTok account as sandbox/test user
7. Copy Client Key + Client Secret to `python-scripts/social-media-analytics/.env`
8. Run once: `python tiktok_auth.py`

### Instagram + Facebook — Not yet started:
1. Create Meta Developer App at developers.facebook.com (was previously blocked by email verification error — try again or use incognito)
2. Add products: Instagram Graph API + Facebook Login for Business
3. Get long-lived token from Graph API Explorer with permissions: `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement`, `pages_show_list`, `read_insights`
4. Exchange for 60-day token via: `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN`
5. Get Facebook Page ID: `GET /me/accounts`
6. Get Instagram Business Account ID: `GET /{PAGE_ID}?fields=instagram_business_account`
7. Add to `.env`: `META_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `FACEBOOK_PAGE_ID`

**After all setup complete:** Run `python main.py` — new platform tabs appear in the Google Sheet automatically.

---

### Content Researcher (`python-scripts/content-researcher/`)
An on-demand outlier video research tool. Type a video concept → get a full research report with hooks, script, and performance analysis written to Notion.

**What it does:**
- Generates 4 YouTube search query variants from your concept (Claude Haiku)
- Searches YouTube, collects ~60 videos, fetches subscriber counts
- Ranks by views-to-subscriber ratio (surfaces hidden viral gems, not just big channels)
- Pulls first 90s transcripts from top 10 outliers (hook extraction)
- One Claude Sonnet call generates a 9-section report: performance data, why each video was an outlier, top 5 hook patterns, format/length recommendations, keywords, 5 mini hooks, script outline, full word-for-word script draft, pacing & sound design notes
- Writes report to a new Notion page + saves local .md file in `results/`
- Caches results for 7 days — same concept = instant re-run, $0 cost

**Key files:**
- `main.py` — CLI orchestrator: `python main.py "your video concept"`
- `searcher.py` — YouTube search + subscriber count fetching
- `outlier.py` — views/subscriber ratio scoring + ranking
- `transcript.py` — youtube-transcript-api hook extraction (first 90s)
- `analyzer.py` — Claude Sonnet batch analysis (one call, all 9 sections)
- `notion_writer.py` — writes formatted report to new Notion page
- `cache.py` — 7-day disk cache (MD5 key by concept)

**Stack:** Python, Claude (claude-haiku-4-5 for query gen, claude-sonnet-4-6 for analysis), YouTube Data API v3, youtube-transcript-api, Notion API, python-dotenv

**Cost per run:** ~$0.04–0.06. Same concept within 7 days = $0.

**Notion setup:** Add `NOTION_TOKEN` + `NOTION_PAGE_ID` to `.env` — report prints to terminal if not set.

**OAuth:** Shares `client_secret.json` from `../social-media-analytics/`. First run opens browser for YouTube auth (saves `token.json` locally).

**V2 roadmap:** Reddit research layer, TikTok (when developer setup done), Google Trends

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

### Content Researcher
```bash
cd python-scripts/content-researcher
python main.py "your video concept"
```
- First run: opens browser for YouTube OAuth (one-time)
- Requires: `.env` with `ANTHROPIC_API_KEY` + optional `NOTION_TOKEN` + `NOTION_PAGE_ID`

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

### Content Researcher (`python-scripts/content-researcher/.env`)
- `ANTHROPIC_API_KEY` — Claude API key
- `NOTION_TOKEN` — (optional) Notion integration token
- `NOTION_PAGE_ID` — (optional) parent Notion page for research reports

### Social Media Scraper (`python-scripts/social-media-analytics/.env`)
- `ANTHROPIC_API_KEY` — Claude API key
- `SHEET_ID` — auto-filled on first run
- `NOTION_TOKEN` — (optional) Notion integration token
- `NOTION_PAGE_ID` — (optional) parent Notion page for weekly reports
- `META_ACCESS_TOKEN` — 60-day long-lived Meta Page Access Token (Instagram + Facebook)
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` — IG business account ID (from Meta Graph API Explorer)
- `FACEBOOK_PAGE_ID` — Facebook Page ID
- `TIKTOK_CLIENT_KEY` — TikTok app client key (from developers.tiktok.com)
- `TIKTOK_CLIENT_SECRET` — TikTok app client secret

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
