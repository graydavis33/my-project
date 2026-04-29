# Current Priorities

_Last updated: 2026-04-28 (evening) — First production run of the `video-use` AI editor end-to-end on Sai footage (D:/Sai/02_ORGANIZED/2026-04-28/, 3 clips, 3:20 source → 32s final cut). ElevenLabs Scribe transcription + Claude reasoning over `takes_packed.md` + `render.py` per-segment extract → concat → loudnorm. Standard 3-file deliverable in `D:/Sai/AI Edits/<date>/`: final.mp4 + edl.json (cut log + reasoning baked in) + master.srt. Cost ~$0.02 (Scribe only). Re-edits free. Workflow validated: edit-same-day, organize-next-day cadence keeps video-use and footage-organizer from ever touching the same folder. Earlier same-day: Footage Organizer v2 hardening — added `--format` and `--top-level-only` flags, changed `--source` default copy→move, patched `cli_index.py` to skip `Adobe Premiere Pro *` subdirs (was indexing 585 fake preview clips), categorized 84 real clips across 04-19 through 04-27 ($0.18). Final index: 238 real clips. Deferred: folder-structure refactor pending A/B/C choice; Premiere project for 04-27 should relocate to `03_ACTIVE_PROJECTS/`._
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
| 8 | Footage Organizer | 8/12 | v2 LIVE + hardened 2026-04-28. Index has 238 real clips (Premiere preview noise filtered). New flags: `--format <long-form\|short-form>` overrides orientation (now needed since Sai shoots horizontal shorts), `--top-level-only` skips subdirs. `--source` defaults to MOVE now. Pending: folder-structure refactor to `<category>/<date>/` everywhere (Gray to pick A/B/C); pull test on real data; relocate 2026-04-27 Premiere project out of `02_ORGANIZED/`. | Get A/B/C answer → `/create-plan` for the structure refactor → migrate existing 7 dated folders → re-index → real pull test. |

## Recently Completed

- Social Media Analytics — all 4 platforms live (YouTube, TikTok, Instagram, Facebook)
- Invoice System — receipt scanner fully fixed, expenses + dates auto-logged, mileage columns added
- Payday Checklist — built, live on GitHub Pages. Auto-expense sync via Gmail + Claude Haiku + GitHub Actions. Budget countdown UI shows remaining per category. **Updated 2026-04-15:** expanded Gmail query (25+ vendor domains, Venmo/Zelle/PayPal P2P), rent payee exclusions (EXCLUDED_VENDORS in config.py), category overrides for known contacts (CATEGORY_OVERRIDES). Bank statement CSV integration designed but deferred. **Updated 2026-04-21:** UI pass — Emergency Fund goal now editable (dashed-underline input), new Engagement Ring tracker ($10K goal, $300/mo pace), removed redundant "Set aside expense budget" checkoff step, simplified "Transfer to emergency fund" step to show only the auto-synced editable goal, fixed budget-label alignment, legacy history entries auto-migrate on load.

## Ongoing / Always Active

- Email Agent — runs hourly 7am–8pm (LIVE on Mac + VPS — duplicate-run question pending resolution; Approach A iteration in progress, design at docs/superpowers/specs/2026-04-14-email-agent-fix-the-brain-design.md)
- Invoice System — CLI finance tool (LIVE on Mac)
- Dashboard — `dashboard.html` at graydavis33.github.io/my-project/dashboard.html
- **Tool Iteration Initiative** — iterating on all 14 tools one at a time, applying the AI-workflow-video framework. Log at `docs/tool-iteration-log.md`. Currently: Email Agent (iteration #1, mid-flight).
