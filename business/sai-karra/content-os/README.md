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
| `youtube-longform-sop.md` | Bi-Weekly cinematic long-form (in-progress, finalizing before handoff) |
| `linkedin-sop.md` | LinkedIn — **OUTSOURCED**: a 3rd-party AI tool interviews Sai + drafts the posts; Gray adds images + reviews; post daily |


## Production tiers (quick reference)

| Tier | Production | Cadence | Owner |
|---|---|---|---|
| Short-form (TikTok / IG Reels / YT Shorts) | LOW (~3 min/edit) | 5-10+/day | Sai films, Gray edits |
| Stories (IG + TikTok) | NONE | ≥3/day | Sai + Gray when together |
| Long-form YouTube | HIGH | Weekly | Gray |
| Paid Ads (Trendify) | HIGH | Per need | Gray + Editor team |
| LinkedIn | LOW (outsourced) | Daily | 3rd-party AI interviews Sai + drafts → Gray adds images + reviews |

**Rule:** Each platform has its own strategy. Strategies do NOT cross-pollinate.

---

## Active deliverables (Gray, Creative Director)

- [ ] Build out the per-platform SOPs in this folder
- [ ] Stand up Asana for editing pipeline status
- [ ] Finalize `youtube-longform-sop.md` before handoff
- [ ] 3 thumbnail options per long-form video going forward
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

### LINKEDIN (OUTSOURCED)
1. **Interview** — Sai talks to a 3rd-party AI tool that gathers data, interviews him, and drafts the posts — 🟢 live (external)
2. **Images** — Gray adds pictures to each post — 🟢 Gray
3. **Review** — Gray reviews the drafts before they go out — 🟢 Gray
4. **Post** — daily — 🟢 live
5. **Reusable image Drive** — a stock of visuals to pull from — 🟡 planned
6. **Repurpose** — into carousels / stories / BTS culture videos (recruiting) — 🟡 planned

_Our `python-scripts/sai-linkedin` tool is superseded for LinkedIn drafting by the outsourced AI-interview tool._

### What changed (2026-06-14 review)
- **Variety is the mandate** — formats, graphics, content types (shorts were too samey).
- **Long-form = STORY, not tutorial** — map the arc + lock title/thumbnail before the A-roll; one story per video.
- **Instagram is the priority platform; retention is the only shorts metric Sai cares about.**
- **Division of labor:** Gray owns format + topics (from daily notes); Sai scripts the words.
- **New rule:** A/B/C trial-reel hooks must differ VISUALLY, not just verbally.
- **New tooling:** `story-arc-board`, two reusable editable-HTML review generators (batch + interview), Sandcastles-cross-merge scripting.
- **2026-06-15:** LinkedIn is now **outsourced** (3rd-party AI interviews Sai + drafts; Gray adds images + reviews; daily). **Founder Series is retired.** Long-form cadence is bi-weekly.

Full review + backlog: `business/social-media/sai/reviews/2026-06-14-production-system-review.md` + `SYSTEM-BACKLOG.md`.
