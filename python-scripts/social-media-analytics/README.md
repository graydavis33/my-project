# Social Media Analytics

## What It Does
- Fetches analytics from YouTube, TikTok, Instagram, Facebook
- Writes to Google Sheets (one tab per platform + shared tabs)
- AI insights via Claude Haiku (cached daily)
- Runs weekly via GitHub Actions (every Sunday 9 AM EST)

## Key Files
- `main.py` — orchestrates fetch → AI insights → Sheets
- `youtube_fetcher.py` — YouTube Data API v3 + Analytics API (Google OAuth2)
- `meta_scraper.py` — Instagram + Facebook via Playwright (browser automation — no API needed)
- `meta_fetcher.py` — OLD: Instagram + Facebook via Meta Graph API (kept for reference, not used)
- `tiktok_fetcher.py` — TikTok Display API with cursor pagination + auto token refresh
- `tiktok_auth.py` — one-time TikTok OAuth2 browser flow
- `ai_analyzer.py` — Claude analysis (Haiku cached)
- `sheets_writer.py` — platform-agnostic Google Sheets output

## Stack
Python, Claude (claude-haiku-4-5), YouTube Data API v3, Playwright (Instagram/Facebook), TikTok Display API, gspread

## Run
```bash
cd python-scripts/social-media-analytics && python -X utf8 main.py
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `SHEET_ID`
`META_EMAIL`, `META_PASSWORD`, `IG_USERNAME`, `FB_PAGE_SLUG`
`TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`

## Platform Status (as of 2026-03-20)
| Platform | Method | Status |
|----------|--------|--------|
| YouTube | Google OAuth2 API | ⚠️ Needs re-auth (see below) |
| Instagram | Playwright browser scraper | ✅ LIVE — 17 posts scraped |
| Facebook | Playwright browser scraper | ✅ LIVE — posts scraped |
| TikTok | TikTok Display API | ✅ Set up (auth done 2026-03-19) |

## Instagram/Facebook — How It Works (Playwright)
- `meta_scraper.py` logs into Instagram/Facebook using `META_EMAIL` + `META_PASSWORD`
- No API keys, no developer accounts, no approval process needed
- Scrapes post metrics (likes, views, captions, dates) directly from the web UI
- Set `SCRAPER_HEADLESS=false` in .env to watch the browser (debugging)
- Set `SCRAPER_MAX_POSTS=50` to control how many posts to scrape per platform

## ⚠️ Action Needed — Google OAuth Re-Auth
`token.json` expired. YouTube fetch and Google Sheets write both fail until re-authenticated.

**Fix (run once, takes 30 seconds):**
```bash
cd python-scripts/social-media-analytics
python auth.py
```
This opens a browser → log in with your Google account → done. Creates a new `token.json`.

## Token Management
- YouTube/Sheets: OAuth2 via `token.json` — re-run `python auth.py` if expired
- TikTok: access token (~24h) auto-refreshes on 401; refresh token lasts 365 days (`tiktok_token.json`)
- Instagram/Facebook: session-based via Playwright — no tokens needed
