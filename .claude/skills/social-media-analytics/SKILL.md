---
name: social-media-analytics
description: Pull YouTube, TikTok, Instagram, and Facebook analytics into Google Sheets and feed performance data into the iteration system. Triggers when Gray says "pull analytics", "run the scraper", "what did my posts do this week", "update the sheet", or asks about social performance. Wraps python-scripts/social-media-analytics/.
---

# Social Media Analytics

> ⚠️ SKELETON — fill in when this tool graduates from Agent → Orchestrated (see `docs/tool-inventory.md`).

## When to use
- Weekly analytics pull (Sunday review)
- Ad-hoc: "How did [video] perform?"
- Feeding performance data into Layer 7 (Iteration & Tagging)

## Current stage: Agent
## Target stage: Orchestrated (data feeds Analytical SaaS backend)

## Platforms (all LIVE)
- **YouTube** — Google OAuth (see google-oauth-refresh skill if it breaks)
- **TikTok** — credentials in .env, auto-refreshes on 401
- **Instagram** — Playwright scraper (`meta_scraper.py`) — NOT Graph API
- **Facebook** — same Playwright scraper

## Data source decision
Playwright scraping, NOT Meta Graph API. `meta_fetcher.py` kept for reference but not used. Do not suggest the Graph API path as a fix — see `project_social_analytics_meta_shift.md` for rationale.

## Flow

1. Pull 4 platforms → normalized row format
2. Write to Google Sheet tabs (YouTube Shorts, YouTube Longform, Instagram, Facebook, Comments, Best Posting Day, Dashboard)
3. **(Next unlock)** Feed normalized data into Analytical SaaS backend
4. **(Layer 7 integration)** Tag each row with series/pillar/hook/format from video-log.csv
5. **(Layer 7 integration)** Flag 3-strike candidates after 7-day performance window

## Sheet
https://docs.google.com/spreadsheets/d/19xls01LAgXzhwR970geSjABFtWTd1GhQ6-goBLv6FMI

## Known gaps
- Not yet wired into Analytical SaaS backend
- No automatic tagging from video-log.csv (Layer 7)
- Still runs on Windows Task Scheduler — Q2 goal is to move to GitHub Actions

## Run commands
```
cd python-scripts/social-media-analytics && python main.py
```
