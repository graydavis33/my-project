# Workflow: Content Researcher

**Status:** LIVE on Mac + Windows
**Cost:** ~$0.04–0.06/run | Same concept within 7 days = $0 (cached)
**Script:** `python-scripts/content-researcher/`

---

## Objective

Given a video concept, Claude runs an agentic loop — calling search tools on YouTube + Reddit, then writing a 10-section research report: hooks, keywords, script outline, full draft, and pacing notes.

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

## What It Does (Agentic Loop)

Claude Sonnet drives the research via a tool-use loop — it decides when to search, what to pull, and when it has enough context to write the final report. The tools available to it:

- `search_youtube(query)` — generates query variants, runs them, returns ranked Shorts (≤3 min, ranked by views÷subscribers)
- `fetch_transcripts(video_ids)` — pulls first 90s of transcripts for hook extraction
- `search_reddit(query)` — surfaces top-relevant Reddit discussions on the concept
- `finish(report)` — hands back the final 10-section report

Typical run: 3–6 tool calls, then a single final Sonnet completion for the report. Cache (`results/.cache.json`) is a 7-day TTL keyed by normalized concept — same phrasing = $0 instant rerun.

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

- Google Trends integration — validate topic momentum before producing content
- Longform mode — toggle `MAX_DURATION_SECONDS` to allow 4–20 min research targets (currently hard-locked to Shorts)
