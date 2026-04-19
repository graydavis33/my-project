# Current Priorities

_Last updated: 2026-04-19 — Content Pipeline .env created on Mac; Obsidian MCP path updated to Google Drive vault; sai-karra folder confirmed in vault; voice memo → meeting notes workflow ready (pending first memo drop). Shooting-script companion docs created for every Sai format + series._
_Update this file whenever your focus shifts._

> **⚡ MAJOR FOCUS SHIFT 2026-04-15:** Sai Karra job begins — 5h filming + 3h editing daily, 1 short/day + 1 LinkedIn/day + 1 long-form/week. Primary income + primary creative output. Debrief materials at `plans/2026-04-15-sai-debrief-content-strategy.md` (strategy), `plans/2026-04-15-sai-debrief-research-deepdive.md` (intel dump), `plans/2026-04-15-sai-footage-organization-system.md` (filing system), `plans/2026-04-16-sai-format-shooting-scripts.md` (on-set shooting scripts for every format + series). All internal-project work below secondary to Sai deliverables until stable cadence established (~Day 30).

## Scoring Framework

Each project scored 0–3 across 4 dimensions:
1. Unblocks something else
2. Direct revenue or time impact
3. Showcase / social media value
4. Builds toward a sellable product

**Tiebreaker:** simpler/faster project goes first.

---

## Active Priority List

| # | Project | Score | Status | Next Action |
|---|---------|-------|--------|-------------|
| 1 | Content Pipeline | 9/12 | .env created on Mac 2026-04-19. Obsidian path in config.py needs fix (points at wrong Google Drive path). Voice memo → meeting notes workflow ready — waiting on first memo | Drop a voice memo in input/, run python main.py "input/memo.m4a" --meeting-notes. Fix config.py Obsidian path first. |
| 2 | Content Researcher | 9/12 | LIVE on Windows + Mac (agent loop + Reddit already exist) | Docs out of date — content-researcher.md describes old 5-step pipeline, actual code is agentic |
| 3 | Client Onboarding | 7/12 | Built on Windows | Fill .env, review contract template |
| — | Social Media Analytics | 9/12 | LIVE — Instagram data broken (scraper) | Meta app configured (4 permissions added) — next: get access token from Graph API Explorer, add to .env, swap main.py to meta_fetcher |
| 5 | Hook Optimizer | 6/12 | LIVE on Windows (real .env key set 2026-04-13) | Add .env on Mac |
| 6 | Creator Intel | 5/12 | Built on Windows | Needs YouTube OAuth |
| 7 | Morning Briefing | 4/12 | Built on Windows | Needs full .env setup |

## Recently Completed

- Social Media Analytics — all 4 platforms live (YouTube, TikTok, Instagram, Facebook)
- Invoice System — receipt scanner fully fixed, expenses + dates auto-logged, mileage columns added
- Payday Checklist — built, live on GitHub Pages. Auto-expense sync via Gmail + Claude Haiku + GitHub Actions. Budget countdown UI shows remaining per category. **Updated 2026-04-15:** expanded Gmail query (25+ vendor domains, Venmo/Zelle/PayPal P2P), rent payee exclusions (EXCLUDED_VENDORS in config.py), category overrides for known contacts (CATEGORY_OVERRIDES). Bank statement CSV integration designed but deferred.
- Footage Organizer — rebuilt 2026-04-16 with 00–07 numbered folder structure, Sai + Graydient libraries on /Volumes/Footage, first real FX3 test run in progress

## Ongoing / Always Active

- Email Agent — runs hourly 7am–8pm (LIVE on Mac + VPS — duplicate-run question pending resolution; Approach A iteration in progress, design at docs/superpowers/specs/2026-04-14-email-agent-fix-the-brain-design.md)
- Invoice System — CLI finance tool (LIVE on Mac)
- Dashboard — `dashboard.html` at graydavis33.github.io/my-project/dashboard.html
- **Tool Iteration Initiative** — iterating on all 14 tools one at a time, applying the AI-workflow-video framework. Log at `docs/tool-iteration-log.md`. Currently: Email Agent (iteration #1, mid-flight).
