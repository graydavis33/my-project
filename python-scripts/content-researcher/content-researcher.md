# Content Researcher

## What It Does
- Generates 4 YouTube search query variants from your concept (Claude Haiku)
- Searches YouTube, collects ~60 videos, fetches subscriber counts
- Ranks by views-to-subscriber ratio — **Shorts only (≤3 min)**
- Pulls first 90s transcripts from top 10 outliers for hook extraction
- One Sonnet call → 9-section report: hooks, keywords, script outline, full draft, pacing notes
- Outputs styled HTML report (dark theme, auto-opens in browser) + `.md` backup
- 7-day cache — same concept = instant re-run, $0 cost

## Key Files
- `main.py` — orchestration
- `searcher.py` — generates query variants, searches YouTube, fetches metadata + subscriber counts
- `outlier.py` — filters (≤3 min, ≥1k views) and ranks by views÷subscribers
- `transcript.py` — pulls first 90s of transcripts via youtube-transcript-api
- `analyzer.py` — Claude Sonnet report generation
- `html_writer.py` — converts report to styled HTML, saves to `results/`, auto-opens browser
- `cache.py` — 7-day disk cache in `results/.cache.json`

## Stack
Python, Claude (claude-haiku-4-5 query gen, claude-sonnet-4-6 analysis), YouTube Data API v3, youtube-transcript-api

## Run
```bash
cd python-scripts/content-researcher && python main.py "your video concept"
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`, `YOUTUBE_API_KEY`

## Status
LIVE on Mac. Uses simple API key auth (no OAuth needed).

## Notes
- `MAX_DURATION_SECONDS = 180` in `outlier.py` — strictly no longform
- Cost: ~$0.04–0.06/run. Same concept within 7 days = $0
- Results saved to `results/` folder
