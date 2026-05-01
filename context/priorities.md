# Current Priorities

_Last updated: 2026-04-30 — Big AI-editing session. (1) Built a 21-clip vertical day-in-life montage from `D:\Sai\02_ORGANIZED\B-roll and A-roll` — chronological by capture metadata, 4.5s per clip with windows picked by HSV-skin-exposure + frame-diff motion scoring, orange `#F28129` "X:XX pm" timestamp matching the `mastery draft 4.mp4` reference style. Output at `D:\Sai\AI Edits\2026-04-30\final.mp4` (timestamped) + `final_no_timestamps.mp4`. (2) Scaffolded **Remotion Studio** project at `web-apps/remotion-sai-vlog/` with Zod-schema-driven prop editing for clips/text/color/font-size in the right sidebar. Studio runs locally at `localhost:3000` via `npm start`. Note: Remotion's "open in editor" is blocked on Windows by the space in "Gray Davis" — must edit `.tsx` files in VS Code directly. (3) Built dual-cam long-form pipeline for `D:\Sai\A-Roll Long Lessons I learned from growing a business\` — audio cross-correlation (B started +51.57s after A), Whisper-large-v3 transcription on RTX 5070 (82s for 18 min), Claude Sonnet 4.5 picks best takes, output two synced MP4s at `D:\Sai\AI Edits\2026-04-30\long-form\final_Aroll.mp4` + `final_Broll.mp4`, both 578.78s exactly, frame-locked cuts. 18:40 → 9:39 (47% trim). (4) Resolved the paused 37-commit footage-organizer-v2 rebase — took HEAD content for all 6 conflicts; queue collapsed several duplicate "Session update" commits as already-upstream. Earlier (Mac, 2026-04-28): First production run of `video-use` AI editor on Sai 2026-04-28 footage (3:20 → 32s, ~$0.02). Footage Organizer v2 hardening — `--format` and `--top-level-only` flags added, `--source` default copy→move, `cli_index.py` skips `Adobe Premiere Pro *` subdirs (was indexing 585 fake preview clips). Final index: 238 real clips. Earlier: Started brainstorming the **LinkedIn Production System** for Sai. Trigger = Short publishes → transcribe → draft LinkedIn post in Sai's voice → pair with old footage screenshot → publish. Brainstorm paused at Question 1 of ~5 on Mac. Built `python-scripts/gdocs-cli/` and the "Karra Media Automation" Google Cloud project under gray@karramedia.com (separate from graydavis33's social-media-analytics-488803). Used it for Ari Goren recommendation letter + Trendify Props Title Pages doc._
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
| 8 | Footage Organizer | 8/12 | v2 LIVE on `feature/footage-organizer-v2`. Index has 238 real clips at `D:/Sai/.footage-index.sqlite` (Premiere preview noise filtered out). Flags: `--format <long-form\|short-form>` (overrides orientation — needed since Sai shoots horizontal shorts), `--top-level-only` (skips subdirs), `--source` defaults to MOVE. Pull command: `python cli_index.py --client sai pull --orientation vertical --filmed-date YYYY-MM-DD` builds Premiere-ready hardlink folders. Flatten refactor (ORGANIZED → `<category>/<date>/`) Steps 0-3 partially shipped; Steps 4-8 pending. **Rebase onto `308b4cd` resolved 2026-04-30** (was paused mid-flight, completed by taking HEAD content for all 6 conflicts). | Finish flatten refactor: add `--allow-today` flag, write migration script, run on 7 dated folders, re-index, update workflow + README, real pull test, relocate 2026-04-27 Premiere project out of `02_ORGANIZED/`. Phase 2 (Whisper transcripts + semantic search) deferred. |

## Recently Completed

- Social Media Analytics — all 4 platforms live (YouTube, TikTok, Instagram, Facebook)
- Invoice System — receipt scanner fully fixed, expenses + dates auto-logged, mileage columns added
- Payday Checklist — built, live on GitHub Pages. Auto-expense sync via Gmail + Claude Haiku + GitHub Actions. Budget countdown UI shows remaining per category. **Updated 2026-04-15:** expanded Gmail query (25+ vendor domains, Venmo/Zelle/PayPal P2P), rent payee exclusions (EXCLUDED_VENDORS in config.py), category overrides for known contacts (CATEGORY_OVERRIDES). Bank statement CSV integration designed but deferred. **Updated 2026-04-21:** UI pass — Emergency Fund goal now editable (dashed-underline input), new Engagement Ring tracker ($10K goal, $300/mo pace), removed redundant "Set aside expense budget" checkoff step, simplified "Transfer to emergency fund" step to show only the auto-synced editable goal, fixed budget-label alignment, legacy history entries auto-migrate on load.

## Ongoing / Always Active

- Email Agent — runs hourly 7am–8pm (LIVE on Mac + VPS — duplicate-run question pending resolution; Approach A iteration in progress, design at docs/superpowers/specs/2026-04-14-email-agent-fix-the-brain-design.md)
- Invoice System — CLI finance tool (LIVE on Mac)
- Dashboard — `dashboard.html` at graydavis33.github.io/my-project/dashboard.html
- **Tool Iteration Initiative** — iterating on all 14 tools one at a time, applying the AI-workflow-video framework. Log at `docs/tool-iteration-log.md`. Currently: Email Agent (iteration #1, mid-flight).
