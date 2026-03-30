# Workflow: Content Researcher

**Status:** LIVE on Mac
**Cost:** ~$0.04–0.06/run | Same concept within 7 days = $0 (cached)
**Script:** `python-scripts/content-researcher/`

---

## Objective

Given a video concept, find the top-performing YouTube Shorts on that topic and generate a full research report: hooks, keywords, script outline, full draft, and pacing notes.

---

## Inputs Required

- A video concept or topic (plain English string)
  - Example: `"how to film cinematic broll on a budget"`

---

## How to Run

```bash
cd python-scripts/content-researcher
python main.py "your video concept"
```

Output: styled HTML report auto-opens in browser + `.md` backup saved to `results/`

---

## What It Does (Step by Step)

1. Claude Haiku generates 4 YouTube search query variants from the concept
2. Searches YouTube, collects ~60 videos, fetches subscriber counts
3. Filters: Shorts only (≤3 min, ≥1k views), ranks by views÷subscribers ratio
4. Pulls first 90s transcripts from top 10 outlier videos
5. Claude Sonnet generates 9-section report: hooks, keywords, script outline, full draft, pacing

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| YouTube API quota error | Wait until midnight (quota resets daily). Check `YOUTUBE_API_KEY` in `.env`. |
| No transcripts found | Normal for some videos — report still generates, just with fewer hook examples |
| Report looks thin | Try a more specific concept. Broad topics return generic results. |
| Re-running same concept | Cache is 7 days. To force a fresh run, delete `results/.cache.json` |
| Missing `.env` vars | Needs `ANTHROPIC_API_KEY` + `YOUTUBE_API_KEY` — both required |

---

## Known Constraints

- Only searches YouTube Shorts (≤3 min) — by design
- YouTube Data API has a daily quota — don't run more than ~5x/day on the same key
- Notion output requires optional `NOTION_TOKEN` + `NOTION_PAGE_ID` in `.env` — otherwise report prints to terminal only

---

## V2 Backlog (Not Yet Built)

- Reddit layer — search Reddit for top posts on the concept to surface what people are actually asking
- Google Trends integration — validate topic momentum before producing content
