# Social Media Analytics

## What It Does
- Fetches analytics from YouTube, TikTok, Instagram, Facebook
- Writes to Google Sheets (one tab per platform + shared tabs)
- AI insights via Claude Haiku (cached daily)
- Runs weekly via GitHub Actions (every Sunday 9 AM EST)

## Key Files
- `main.py` — orchestrates fetch → AI insights → Sheets
- `youtube_fetcher.py` — YouTube Data API v3 + Analytics API (Google OAuth2)
- `meta_fetcher.py` — Instagram + Facebook via Meta Graph API v19.0
- `tiktok_fetcher.py` — TikTok Display API with cursor pagination + auto token refresh
- `tiktok_auth.py` — one-time TikTok OAuth2 browser flow
- `ai_analyzer.py` — Claude analysis (Haiku cached)
- `sheets_writer.py` — platform-agnostic Google Sheets output

## Stack
Python, Claude (claude-haiku-4-5), YouTube Data API v3, Meta Graph API v19.0, TikTok Display API, gspread

## Run
```bash
cd python-scripts/social-media-analytics && python main.py
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `SHEET_ID`, `META_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `FACEBOOK_PAGE_ID`, `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`

## Token Management
- YouTube: OAuth2 token auto-refreshes (`token.json`)
- Meta: 60-day long-lived token — refresh manually every 60 days
- TikTok: access token (~24h) auto-refreshes on 401; refresh token lasts 365 days (`tiktok_token.json`)

## Status
BLOCKED — TikTok and Instagram/Facebook API setup incomplete.

## TikTok — UNBLOCKED (as of 2026-03-19)
Setup complete. Env vars set, auth flow done.

## Pending Setup (Instagram + Facebook)
1. Create Meta Developer App — add Instagram Graph API + Facebook Login for Business
2. Get long-lived token from Graph API Explorer
3. Exchange for 60-day token, get Page ID and Instagram Business Account ID
4. Add `META_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `FACEBOOK_PAGE_ID` to `.env`
