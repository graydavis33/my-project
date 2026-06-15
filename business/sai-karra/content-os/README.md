# Sai Karra — Content Operating System

**Locked:** 2026-05-10 (per [[Month 1 Recap]] voice memo)
**Active:** Tuesday 2026-05-26 (ground-running date)
**Canonical doc:** `C:/Users/Gray Davis/My Drive/Obsidian/Graydient Media/sai-karra/Content Operating System.md`

This folder is the workspace-side mirror — for SOPs that need to live next to code (e.g., referenced by python-scripts/sai-linkedin, transcriber, etc.). The Obsidian doc is the canonical strategy + narrative source. The SOPs here are the operational checklists.

---

## Files

| File | Purpose |
|---|---|
| `pre-post-checklist.md` | The 4-question gate every post passes before shipping (Honest / Craft / Value / True) |
| `tiktok-sop.md` | Daily TikTok workflow — raw UGC short-form |
| `instagram-reels-sop.md` | Daily IG Reels workflow — Trial Reels |
| `instagram-stories-sop.md` | Daily IG Stories — ≥3/day for retention |
| `youtube-shorts-sop.md` | Daily YT Shorts — same edit as TikTok/Reels |
| `youtube-longform-sop.md` | Weekly cinematic long-form (in-progress, finalizing before handoff) |
| `linkedin-sop.md` | LinkedIn — business-focused, NOT IG repurpose (awaiting Sai's direction) |
| `founder-series-sop.md` | Founder Series interview workflow |

---

## Production tiers (quick reference)

| Tier | Production | Cadence | Owner |
|---|---|---|---|
| Short-form (TikTok / IG Reels / YT Shorts) | LOW (~3 min/edit) | 5-10+/day | Sai films, Gray edits |
| Stories (IG + TikTok) | NONE | ≥3/day | Sai + Gray when together |
| Long-form YouTube | HIGH | Weekly | Gray |
| Founder Series | HIGH | Ad-hoc | Gray |
| Paid Ads (Trendify) | HIGH | Per need | Gray + Editor team |
| LinkedIn | MEDIUM | Daily target | Sai writes → Gray drafts |

**Rule:** Each platform has its own strategy. Strategies do NOT cross-pollinate.

---

## Active deliverables (Gray, Creative Director)

- [ ] Build out the per-platform SOPs in this folder
- [ ] Stand up Asana for editing pipeline status
- [ ] Finalize `youtube-longform-sop.md` before handoff
- [ ] 3 thumbnail options per long-form video going forward
- [ ] Edit Founder Series long-form (raw footage, no time-cost)
- [ ] Build content-alignment theses dashboard (what worked + why)
- [ ] Develop funnel map: shorts → long-form → podcast → LinkedIn

## Active deliverables (Sai)

- [ ] Stockpile 20+ UGC clips during the 5/10-5/26 window
- [ ] Send LinkedIn content direction within a few days
- [ ] Begin trial-reels testing with volume

---

## The hard rules

1. **No virality-as-goal.** No vanity metrics.
2. **No IG → LinkedIn repurpose.** LinkedIn is business-focused, custom.
3. **No B-roll, no music, no HyperFrames assets on daily UGC shorts.** Strip-down editing only.
4. **5/03 "Day X of building Trendify" cinematic daily diary is DEAD.** Do not propose it.
5. **Every post passes the pre-post checklist or it doesn't ship.**
6. **Track views-to-followers conversion %, not raw views.**

---

## Pipeline — stages & status (updated 2026-06-15, from the 2026-06-14 production-system review)

Status: 🟢 built/live · 🟡 planned/next. This is the living map of the COS as we build it.

### SHORTS
1. **Capture** — Gray's end-of-day on-set notes (interesting moments → short ideas) — 🟡 planned
2. **Plan** — weekly format MENU + topics in Notion; Sai approves/swaps morning-of — 🟡 planned
3. **Research** — Sandcastles: proven hooks / formats / top performers in the niche — 🟢 live
4. **Script** — cross-merge Sai's real talking points × proven formats → scriptwriter writes A/B/C hooks, **each with a distinct VISUAL treatment** — 🟢 built (Batch 3)
5. **Review** — editable batch-review HTML (`scripts/.build_batch_review.py`); pick hook, Approve/Swap/Cut, edit text, Sandcastles ref links — 🟢 built
6. **Produce** — film → selects cut + caption layer (`_b2_edit/pipeline.py`) — 🟢 live
7. **Measure** — retention-only dashboard + outlier flag — 🟡 planned

### LONG-FORM (cinematic BTS doc — focus of the 6/15 build)
1. **Transcribe** the week's raw footage (local Whisper) — 🟢 live
2. **Map the story arc** — `story-arc-board` web tool (folder-scoped) + `EP{N}-ARC-MAP.md` — 🟢 built
3. **Lock title + thumbnail** (BEFORE the A-roll) — ideation pass + editable HTML — 🟡 next
4. **Interview questions** derived from the arc — `EP{N}-INTERVIEW-QUESTIONS.md` — 🟢 built (EP2)
5. **Review interview Qs** — editable HTML for Sai (`longform/.build_interview_review.py`) — 🟢 built
6. **Pre-edit pool** — clips duplicated into `07_QUERY_PULLS/EP{N}-arc-map/`, renamed in story order + `_EDIT-GUIDE.md` — 🟢 built (EP2)
7. **Film → Premiere edit** (interview = spine, B-roll cut under it) — 🟢 Gray
8. **Series template** (repeatable skeleton) — `longform/ep2/_SERIES-TEMPLATE.md` — 🟢 exists

### LINKEDIN
1. **Draft** — `python-scripts/sai-linkedin` (keep as-is, Sai loves it) — 🟢 live
2. **Reusable image Drive** — a stock of visuals to choose from — 🟡 planned
3. **Repurpose** — into carousels / stories / BTS culture videos (recruiting) — 🟡 planned

### What changed (2026-06-14 review)
- **Variety is the mandate** — formats, graphics, content types (shorts were too samey).
- **Long-form = STORY, not tutorial** — map the arc + lock title/thumbnail before the A-roll; one story per video.
- **Instagram is the priority platform; retention is the only shorts metric Sai cares about.**
- **Division of labor:** Gray owns format + topics (from daily notes); Sai scripts the words.
- **New rule:** A/B/C trial-reel hooks must differ VISUALLY, not just verbally.
- **New tooling:** `story-arc-board`, two reusable editable-HTML review generators (batch + interview), Sandcastles-cross-merge scripting.

Full review + backlog: `business/social-media/sai/reviews/2026-06-14-production-system-review.md` + `SYSTEM-BACKLOG.md`.
