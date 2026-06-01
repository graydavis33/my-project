---
name: content-researcher
description: Research a video concept end-to-end — finds trending YouTube outliers, Reddit pain points, and Claude-synthesized topic recommendations. Triggers when Gray says "research [topic]", "find videos about [X]", "what's trending in [niche]", or asks for a daily/weekly trend brief. Wraps python-scripts/content-researcher/.
---

# Content Researcher

> ⚠️ SKELETON — fill in when this tool graduates from Assisted → SOP (see `docs/tool-inventory.md`).

## When to use
- "Research [concept]" → single-shot research run
- "Daily trend brief" → automated 3-topic Slack DM (not yet built — `daily_trend_brief()` pending)
- "What's trending on [platform]" → pulls YouTube outliers + Reddit top posts

## Current stage: Assisted
## Target stage: Agent

## Flow

1. Accept input: video concept or keyword
2. Pull: YouTube outliers (3x channel average), Reddit top posts (r/videography, r/premiere, r/editors)
3. Pass through Claude for pattern synthesis
4. Output: Notion page + Slack summary

## Known gaps
- `daily_trend_brief()` function not built
- Workflow docs describe old 5-step pipeline; actual code is agentic
- Google Trends API layer not integrated

## Run commands
```
cd python-scripts/content-researcher && python main.py "your concept"
```

## Cost
~$0.05/run, 7-day cache
