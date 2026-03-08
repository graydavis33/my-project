# Hook + Title Optimizer

## What It Does
- Input a video concept → Claude outputs 5 YouTube titles, 5 TikTok titles, 3 hooks, thumbnail concept, best pick
- Concept cache (MD5 hash, 7-day TTL) — repeats are instant, no API call
- Auto-saves every result to `results/{slug}-{timestamp}.txt`

## Key Files
- `main.py` — CLI entry, cache check, Claude call, save result

## Stack
Python, Claude (claude-sonnet-4-6), python-dotenv

## Run
```bash
cd python-scripts/hook-optimizer && python main.py "your video concept"
```

## Env Vars (.env)
`ANTHROPIC_API_KEY`

## Status
Built on Windows. Needs `.env` setup to run on Mac.
