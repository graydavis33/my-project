---
name: creator-intel
description: Monitor tracked competitor creators, detect outlier videos (3x their channel average), and output Sunday Slack outlier reports. Triggers when Gray says "creator intel", "who's outperforming", "weekly outlier report", "what did [creator] post this week", or runs competitor analysis. Wraps python-scripts/creator-intel/.
---

# Creator Intel

> ⚠️ SKELETON — fill in when this tool graduates from Assisted → Agent (see `docs/tool-inventory.md`).

## When to use
- Weekly Sunday outlier report (target cadence, not yet automated)
- Ad-hoc: "What hit on [creator]'s channel this week?"
- Pattern analysis: "What topics are trending across my tracked list?"

## Current stage: Assisted
## Target stage: Agent

## Tracked creators
- Jordy Vandeput (Cinecom)
- Parker Walbeck
- Mango Street
- Isaiah Photo
- Peter McKinnon
- 2-3 smaller creators (<100k) in AI+video space (TBD — populate when chosen)

## Flow

1. Pull last 7 days of uploads from tracked channels (YouTube Data API)
2. Calculate rolling channel average
3. Flag outliers (>3x channel average views in first 7 days)
4. Extract: hooks (first 3s transcript), topics, format
5. Claude synthesis: pattern recognition across outliers
6. Slack DM: top 5 outliers + takeaways, every Sunday 9am

## Known gaps
- `weekly_outlier_report.py` not built
- Tracked creators list lives in code, not config
- Needs YouTube OAuth (see google-oauth-refresh skill if it breaks)

## Run commands
```
cd python-scripts/creator-intel && python main.py
```
