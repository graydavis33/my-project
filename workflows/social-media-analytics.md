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

1. **Fetch** all four platforms in sequence: YouTube (Data API v3 + OAuth2) → Instagram (Playwright scraper OR Meta Graph API if `META_ACCESS_TOKEN` set) → Facebook (same) → TikTok (Display API, auto token refresh)
2. **Compute** engagement_rate per post ((likes + comments + shares) / views × 100)
3. **AI sheet insights** — one Haiku call, cached daily, produces the tab-level summaries
4. **Best/worst post explanations** — Haiku generates 3-bullet "why this worked" / "why this underperformed" for top 3 + bottom 3 posts by views. Cached per-URL per-day (no re-spend on posts already explained today).
5. **Trends** — searches YouTube for real trending videos in `CONTENT_NICHE` (from `.env`), takes the top 2 by views, Haiku analyzes each into `{what_it_is, why_it_works, how_to_implement}`. Cached daily.
6. **Dashboard JSON export** — writes `web-apps/social-media-analytics/analytics_data.json` with posts + ai_insights + post_explanations + trends (the web dashboard reads this)
7. **Google Sheets write** — platform tabs + Dashboard + Comments + Best Posting Day + Trends
8. **Deep AI analysis → Notion** (optional if `NOTION_TOKEN` set)

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

- **Current:** GitHub Actions — weekly, every Sunday 9am EST (in-cloud, no machine needed)
- Secrets configured in GitHub: `GOOGLE_TOKEN_JSON` (base64 of token.json), `ANTHROPIC_API_KEY`, `SHEET_ID`, `META_*`, `TIKTOK_*`
- Local manual runs still work via `python -X utf8 main.py` — useful for ad-hoc refreshes between weekly runs
- `CONTENT_NICHE` env var controls the trends search query (default: "videography video editing tutorial")

---

## SaaS Vision

This tool is the #1 candidate for monetization. Full roadmap in `python-scripts/social-media-analytics/APP_ROADMAP.md`.
