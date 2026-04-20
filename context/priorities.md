# Current Priorities

_Last updated: 2026-04-20 — Footage Organizer fully live on Mac. `06_BROLL_LIBRARY` renamed to `06_FOOTAGE_LIBRARY` with `unused/` and `used/` subfolders. Auto-delete RAW after organize. `--mark-used DATE` command added. `04_DELIVERED` restructured to format-first (shorts/linkedin/episodes). `miscellaneous` renamed to `misc`. Organized 2026-04-17 (23 clips) + old-broll (15 clips). Archived 2026-04-16, 2026-04-17, 2026-04-18, old-broll into FOOTAGE_LIBRARY/unused/. Note: 2026-04-16 archive landed all 40 clips in misc/ (Windows cache path mismatch — categories lost)._
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
| 1 | Content Pipeline | 9/12 | LIVE on Windows GPU (CUDA 12.8). 10 voice memos transcribed 2026-04-19 → `Voice Memos/` vault folder + index. Filename date-prefix parsing + auto-backlink shipped. | For future memos: drop `.m4a` in `C:/Users/Gray Davis/My Drive/Voice Memos/` with `YYYY-MM-DD - ` prefix, run `python main.py "C:/Users/Gray Davis/My Drive/Voice Memos" --meeting-notes --all`. Upgrade: iOS Shortcut or Just Press Record app to auto-prefix dates. |
| 2 | Content Researcher | 9/12 | LIVE on Windows + Mac (agent loop + Reddit already exist) | Docs out of date — content-researcher.md describes old 5-step pipeline, actual code is agentic |
| 3 | Client Onboarding | 7/12 | Built on Windows | Fill .env, review contract template |
| — | Social Media Analytics | 9/12 | LIVE — Instagram data broken (scraper) | Meta app configured (4 permissions added) — next: get access token from Graph API Explorer, add to .env, swap main.py to meta_fetcher |
| 5 | Hook Optimizer | 6/12 | LIVE on Windows (real .env key set 2026-04-13) | Add .env on Mac |
| 6 | Creator Intel | 5/12 | Built on Windows | Needs YouTube OAuth |
| 7 | Morning Briefing | 4/12 | Built on Windows | Needs full .env setup |
| 8 | Footage Organizer | 8/12 | LIVE on Mac + Windows. Footage Library rebuilt: unused/used split, auto-delete RAW, --mark-used command, format-first Delivered folder. 111 clips archived into FOOTAGE_LIBRARY/unused/ (2026-04-16/17/18 + old-broll). | Build test-set.csv from real misses → run eval.py → tighten prompt → repeat. April 16 clips in misc/ need manual re-sort (Windows cache issue). |

## Recently Completed

- Social Media Analytics — all 4 platforms live (YouTube, TikTok, Instagram, Facebook)
- Invoice System — receipt scanner fully fixed, expenses + dates auto-logged, mileage columns added
- Payday Checklist — built, live on GitHub Pages. Auto-expense sync via Gmail + Claude Haiku + GitHub Actions. Budget countdown UI shows remaining per category. **Updated 2026-04-15:** expanded Gmail query (25+ vendor domains, Venmo/Zelle/PayPal P2P), rent payee exclusions (EXCLUDED_VENDORS in config.py), category overrides for known contacts (CATEGORY_OVERRIDES). Bank statement CSV integration designed but deferred.

## Ongoing / Always Active

- Email Agent — runs hourly 7am–8pm (LIVE on Mac + VPS — duplicate-run question pending resolution; Approach A iteration in progress, design at docs/superpowers/specs/2026-04-14-email-agent-fix-the-brain-design.md)
- Invoice System — CLI finance tool (LIVE on Mac)
- Dashboard — `dashboard.html` at graydavis33.github.io/my-project/dashboard.html
- **Tool Iteration Initiative** — iterating on all 14 tools one at a time, applying the AI-workflow-video framework. Log at `docs/tool-iteration-log.md`. Currently: Email Agent (iteration #1, mid-flight).
