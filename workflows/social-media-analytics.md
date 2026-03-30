# Workflow: Social Media Analytics

**Status:** LIVE — YouTube, TikTok, Instagram, Facebook
**Cost:** Minimal — Claude Haiku cached daily
**Script:** `python-scripts/social-media-analytics/`
**Sheet:** https://docs.google.com/spreadsheets/d/19xls01LAgXzhwR970geSjABFtWTd1GhQ6-goBLv6FMI

---

## Objective

Scrape analytics from all 4 platforms, write to Google Sheets, generate Claude AI insights. Runs automatically every Sunday 9am EST (Windows Task Scheduler). GitHub Actions migration is a Q2 goal.

---

## How to Run (Manual)

```bash
cd python-scripts/social-media-analytics
python -X utf8 main.py
```

---

## What It Does (Step by Step)

1. YouTube: fetches video analytics via YouTube Data API v3 (Google OAuth2)
2. TikTok: fetches post metrics via TikTok Display API (auto token refresh)
3. Instagram: Playwright logs into Instagram, scrapes post metrics from web UI
4. Facebook: Playwright logs into Facebook, scrapes Graydient Media page
5. Claude Haiku generates AI insights across all platforms (cached daily)
6. Writes everything to Google Sheets — one tab per platform

---

## Platform Quick Reference

| Platform | Method | Auth File | Re-auth Command |
|----------|--------|-----------|-----------------|
| YouTube | Google OAuth2 API | `token.json` | `python auth.py` |
| Instagram | Playwright scraper | None — uses META_EMAIL/PASSWORD | N/A |
| Facebook | Playwright scraper | None — uses META_EMAIL/PASSWORD | N/A |
| TikTok | TikTok Display API | `tiktok_token.json` | `python tiktok_auth.py` |

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| YouTube / Sheets auth error | Token expired — run `python auth.py` (opens browser, takes 30 sec) |
| Instagram/Facebook login blocked | Meta session expired — check META_EMAIL + META_PASSWORD in `.env`. Run with `SCRAPER_HEADLESS=false` to debug. |
| TikTok 401 error | Access token expired — auto-refreshes on retry. If persistent, run `python tiktok_auth.py` |
| Sheet not updating | Check `SHEET_ID` in `.env`. Verify Google OAuth token is valid. |
| Script hangs on Playwright | Kill and re-run. Sometimes browser doesn't close cleanly. |

---

## Env Vars Required

```
ANTHROPIC_API_KEY
SHEET_ID
META_EMAIL
META_PASSWORD
IG_USERNAME=graydient_media
FB_PAGE_SLUG=https://www.facebook.com/profile.php?id=61575803340179
TIKTOK_CLIENT_KEY
TIKTOK_CLIENT_SECRET
```

---

## Scheduling

- **Current:** Windows Task Scheduler, every Sunday 8am
- **Goal (Q2):** GitHub Actions workflow — runs in cloud, no machine needed
  - Secrets needed in GitHub: `GOOGLE_TOKEN_JSON` (base64 of token.json), `ANTHROPIC_API_KEY`, `SHEET_ID`

---

## SaaS Vision

This tool is the #1 candidate for monetization. Full roadmap in `python-scripts/social-media-analytics/APP_ROADMAP.md`.
