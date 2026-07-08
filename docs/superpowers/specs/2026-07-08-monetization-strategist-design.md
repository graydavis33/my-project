# Monetization Strategist — Design Spec

**Date:** 2026-07-08
**Status:** Approved by Gray (Approach A — analyze at /save, brief at /prime)
**Author:** Claude + Gray

---

## Purpose

A standing subagent whose only job is monetization. It watches everything Gray builds and discusses (through the artifacts every session already produces), spots sellable products/services/features, scores them against Gray's real constraints, and briefs him daily through /prime with a recommended course of action.

It is a **strategist, not a builder**: it plans and recommends. Nothing gets built without Gray's explicit approval.

**Long-term goal:** income that doesn't require Gray's hours. Transition Graydient Media from pure time-for-money (Sai job + freelance) toward products, templates, and content that sell independently — and de-risk single-client dependence. The agent exists so this transition stops being perpetually deferred ("start monetizing" was a Q2 goal that slipped).

**Timescale expectation:** this is a long-term system. Nothing may surface for six months; three things may surface in a month. Quiet updates are a valid, expected output.

---

## Hard Constraints (from Gray)

1. **Token efficiency.** Never re-read the same files over and over. Incremental analysis only — a cursor tracks what has already been analyzed, and the agent only reads what's new since the cursor. Market research is bounded the same way: targeted checks per candidate, never open-ended crawls.
2. **Side-doable only.** Every opportunity must be shippable and maintainable alongside the Sai job and freelance work. Anything requiring full-time Gray is killed on sight, regardless of upside.
3. **No building without approval.** The agent's output is analysis, plans, and briefs. Building happens in normal sessions after Gray says go.
4. **Daily communication through /prime.** No new notification channels. The brief is short; "nothing new, still watching" is acceptable.

---

## Architecture

Five pieces. No new Python tools, no schedulers, no infrastructure — a subagent definition, two state files, edits to two existing commands, and a one-time backfill.

```
session work
    → /save writes session summary (existing behavior)
        → NEW: spawn monetization-strategist with {summary + changed files}
            → agent reads state.json cursor, analyzes only the delta
            → updates business/monetization/PIPELINE.md
            → bumps cursor in state.json
    → next session: /prime
        → NEW: read PIPELINE.md (no subagent, no analysis)
        → "Monetization Watch" section in the briefing (3–5 lines)
    → Gray reacts ("kill that", "develop this", "I like X")
        → reactions land in the next session summary
        → strategist sees them at next /save → pipeline adjusts
```

### 1. Subagent — `.claude/agents/monetization-strategist.md`

- **Model:** Sonnet (inputs are small; reasoning quality matters more than speed).
- **Tools:** Read, Glob, Grep, Write, Edit, WebSearch, WebFetch. Web research IS allowed in daily runs for market validation, but bounded: only when a candidate is being scored for WATCHLIST/NOW promotion — a handful of targeted searches per candidate (Reddit threads, competitor products and pricing, news, social signals), enough to verify or kill the idea, never an open-ended crawl. RADAR jottings and already-scored entries get no re-research. Deep-dive mode (see below) does the full market workup.
- **Contract:**
  - Read `business/monetization/state.json` first. Only analyze material newer than the cursor.
  - Update `PIPELINE.md` sections as warranted. If the session contains nothing monetization-relevant, bump the cursor and touch nothing else.
  - A candidate cannot enter WATCHLIST without a market check. If the check shows the idea is dead in the real market (saturated, strong free alternatives, no demand signal), it goes straight to KILLED with the evidence links — before Gray ever hears it as a recommendation.
  - Never re-pitch a KILLED idea unless materially new evidence appears (same spirit as the batch no-repeats rule).
  - Never propose building; every NOW recommendation ends in a next action *for Gray to approve*, not an action the agent takes.
  - Keep dollar figures and sensitive business details out of PIPELINE.md (the repo is public).

### 2. State — `business/monetization/`

**`PIPELINE.md`** — the living doc, four sections:

| Section | Contents |
|---|---|
| **NOW** | The single #1 candidate: what it is, why now, scored breakdown, the concrete next action, and the strategist's current take. May be empty ("no candidate meets the bar"). |
| **WATCHLIST** | Scored active ideas — a handful, ruthlessly pruned. Each: one-line pitch, scores, what evidence would promote it to NOW. |
| **RADAR** | Weak signals worth watching, not yet scored. One line each. |
| **KILLED** | Dead ideas with the reason they died and the evidence links that killed them. Append-only. Never re-pitched by the agent without new evidence — but Gray can resurrect any entry on request ("pull X back up"), which triggers a fresh deep-dive. |

**`state.json`** — the cursor:

```json
{
  "last_analyzed_commit": "<hash>",
  "last_analyzed_date": "YYYY-MM-DD",
  "backfill_complete": true,
  "version": 1
}
```

### 3. Scoring model

Each candidate scored 0–3 on five dimensions:

1. **Demand evidence** — has anyone actually shown they'd pay? Verified against the real market (Reddit, competitor products and pricing, news, social signals), not just intuition.
2. **Effort to ship** — Gray-effort to a sellable v1 (lower complexity = higher score)
3. **Maintenance burden** — support/updates burden (lower complexity = higher score)
4. **Distribution fit** — can Gray's existing channels (@graydient_media audience, content brand, network) reach the buyer?
5. **Price potential** — revenue shape: one-time template vs. recurring vs. service

**Hard gate before scoring:** side-doable. Fails the gate → KILLED, not scored.

Product *form* is weighed explicitly: template/structure/info-product (low ongoing cost) ranks ahead of SaaS (support burden) at equal scores.

### 4. `/save` integration (the write)

New step in `.claude/commands/save.md`, after the session summary is written:

- Spawn `monetization-strategist` with: the freshly written session summary + the list of files changed this session (from git).
- The agent does its delta analysis and updates `business/monetization/` before the commit+push step, so pipeline updates ride the session commit.
- Cost profile: one small subagent call per session; near-zero on sessions with nothing relevant.

### 5. `/prime` integration (the read)

New step in `.claude/commands/prime.md`: read `business/monetization/PIPELINE.md` and add a **"Monetization Watch"** section to the briefing:

- Current NOW candidate + recommended course of action (or "quiet, still watching")
- Anything new on RADAR/WATCHLIST since the last brief
- **Any ideas killed since the last brief — named, with the reason** — so Gray can pull one back up if he disagrees
- 3–6 lines. No subagent spawn, no analysis at prime time.

### 6. One-time backfill (separate session, on Gray's explicit go)

Seeds the pipeline by walking everything produced since Claude Code + Obsidian adoption:

- Full git history (commit messages + key file evolution)
- `context/priorities.md` (the session journal — richest single source)
- `decisions/log.md`, memory directory, workspace audit
- Obsidian vault (`Graydient Media`, via MCP)
- Every `python-scripts/*/README.md`, `web-apps/*`, `workflows/*`

Run with parallel scout subagents to keep the main context lean. Output: seeded PIPELINE.md (initial WATCHLIST/RADAR/KILLED + a NOW pick if one clears the bar) and `state.json` cursor set to the backfill commit. **This is the one deliberately token-heavy run** — it happens once, only when Gray says go, and is never repeated (if state.json is ever lost, re-seed the cursor to today; do NOT auto-re-backfill). The backfill session must flip both completion markers — `state.json`'s `backfill_complete` and PIPELINE.md's `_Backfill:` header line — so a stale marker in one file can't be mistaken for a complete backfill.

### Deep-dive mode (on demand)

When Gray says "develop [idea]": one larger strategist run with web research enabled. Output: a product brief — market check, positioning, offer shape, pricing options, effort estimate (complexity terms, never hour quotes), validation plan, and a first step. Saved to `business/monetization/briefs/YYYY-MM-DD-<idea>.md`. Still zero building.

---

## Error handling

- **Missing/corrupt `state.json`:** the strategist reports it and re-seeds the cursor to today. Never auto-rescans history.
- **Mac/Windows divergence:** all state is in the repo; git sync handles it. PIPELINE.md sections are append-friendly to minimize conflicts.
- **Strategist fails mid-/save:** /save continues (commit+push are not blocked by a strategist error); the missed delta is naturally covered next session because the cursor didn't move.

## Privacy note

Repo stays public for now (Gray's call, 2026-07-08): going private on the Free plan would kill GitHub Pages (payday PWA, dashboard, TikTok OAuth callback) and meter Actions past the free quota. The GitHub Pro upgrade path ($4/mo + hourly cron) is documented in `decisions/log.md` if he changes his mind. Consequence for this system: **no dollar amounts, revenue figures, client terms, or anything sensitive in pipeline files** — pitches and scores only.

## Testing

1. Run the strategist once against a synthetic session summary → verify PIPELINE.md updates and cursor bump.
2. Run it against a clearly irrelevant summary → verify cursor bumps and nothing else changes.
3. Run /prime → verify the Monetization Watch section renders from PIPELINE.md.
4. Verify a KILLED idea is not re-pitched when it reappears in a later summary.

## Rules alignment

- Not a new Python tool — subagent + docs, matching existing `.claude/agents/` patterns (scriptwriter, footage-puller).
- One scheduler per job: no scheduler at all — piggybacks on /save and /prime.
- Doc + code same commit: CLAUDE.md (folder map + agents list + commands) updated in the implementation commit.

## Out of scope (v1)

- Autonomous building of any kind
- Slack/notification channels
- Automatic re-backfills
- Revenue tracking / post-launch analytics (revisit if something ships)
