# Niche Creator Intelligence Monitor

## What It Does
- Monitors 12 YouTube creators weekly (pre-loaded in `creators.json`)
- Fetches last 10 videos per creator via YouTube Data API
- One batched Claude call: trending formats, hook styles, best posting days, topic ideas, one action
- Monday 9:30am Slack report
- 6-day cache — won't re-fetch if run within the week

## Key Files
- `main.py` — orchestration + scheduler
- `youtube_fetcher.py` — YouTube Data API (reuses social-media-analytics credentials)
- `analyzer.py` — batched Claude analysis
- `slack_reporter.py` — formats and sends Slack report
- `creators.json` — pre-loaded with 12 creators (McKinnon, Haapoja, Kolder, MKBHD, D'Avella, etc.)
- `config.py` — API keys, schedule

## Stack
Python, Claude (claude-sonnet-4-6), YouTube Data API v3, Slack SDK, python-dotenv, schedule

## Run
```bash
cd python-scripts/creator-intel
python main.py             # run once
python main.py --schedule  # run every Monday 9:30am
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_USER_ID`, `YOUTUBE_CREDENTIALS_PATH` (defaults to `../social-media-analytics/client_secret.json`)

## Status
Built on Windows. Reuses social-media-analytics credentials — no new API setup needed.
