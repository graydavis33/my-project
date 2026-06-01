# Content Playbook Edits — Design Spec (Sub-Project A)

**Version:** 1.0
**Date:** 2026-04-15
**Status:** Draft — awaiting user review
**Parent initiative:** Content OS (master roadmap A → F)
**Target file:** `business/social-media/content-playbook.md`

> **Living Document.** This spec is expected to evolve. Any meaningful change gets a changelog entry below and a line in `decisions/log.md`. Formats, series, rules, and systems described here are designed to be modified, swapped, or killed as real-world data comes in.

---

## Overview

Surgical edits to the existing Graydient Media Creative Director Playbook. No full rewrite. Changes add reality constraints, simplify distribution, update series to match Gray's actual capacity, and add a new Layer 7 (Iteration & Tagging System).

### What changes

| Section | Action |
|---|---|
| New: Capacity & Constraints | Insert after "The Big Picture" |
| Layer 2: Content Series | Replace series list (5 → 7), add Flex Rules, add Pending/Killed stubs |
| Layer 3: Production | Add Long-Form Production Paths subsection |
| Layer 4: Distribution | Simplify to one-video-all-platforms rule |
| New: Layer 7 | Insert after Layer 6 — Iteration & Tagging System |
| Sai pointer | Add reference to future sub-project B playbook |
| Audio Strategy | Move from Layer 4 to Layer 1 (Research) |
| Scheduling Automation | Remove — deferred to sub-project E (Content OS tool) |

### What stays the same

- Layer 1 (Research System) — still valid
- Layer 3 (Production Schedule) — reworked later when B + D land
- Layer 5 (Growth Tactics) — still valid
- Layer 6 (Analytics) — still valid, extended by Layer 7
- Content Pillars (5 pillars, percentage split) — unchanged
- Content OS tool spec (lines 355-374) — superseded by sub-project E, left as-is for now
- 12-month roadmap — aspirational, left as-is

### Also created

- `decisions/content-os-log.md` — dedicated decision log for Content OS sub-projects (A → F) to keep the main `decisions/log.md` from becoming 80% Content OS noise

---

## Section 1 — Capacity & Constraints

Inserted immediately after "The Big Picture" section. Sets real-world guardrails the rest of the playbook operates inside.

```markdown
## CAPACITY & CONSTRAINTS

This playbook is designed around reality, not a fantasy production schedule.

### Time budget
- Sai Karra job: ~40h/week (varies with his schedule) — primary income, non-negotiable
- Content production for Graydient: estimated 5-10h/week realistic ceiling
- No daily uploads. Cadence is volume-capped, not ambition-capped.

### Posting rule (one-video-all-platforms)
Every short-form video gets posted to ALL three short platforms:
- TikTok
- Instagram Reels
- YouTube Shorts

No platform-specific variants. No per-platform re-cuts. Same video,
three uploads. Captions can vary, video cannot.

### Burnout rule
If a week hits its capacity ceiling, we cut content — never Sai, never sleep,
never research. Missed uploads < burned-out creator.

### Automation target
Every stage in Layers 1-7 aims to run without human input except where
human-in-loop is explicitly required (filming myself, on-camera talking,
creative decisions). The goal is not "Gray does less." The goal is
"Gray does only what Gray uniquely can do."
```

---

## Section 2 — Content Series List (Graydient)

Replaces the existing "Content Series" block (lines 140-170 of current playbook). Expands from 5 series to 7. Adds Flex Rules, Pending Ideas stub, and Killed Archive stub.

### Series table

| # | Series | Format | Cadence | Production Style | Long-form Path |
|---|---|---|---|---|---|
| 1 | **Claude Edits** | Short-form | Weekly | Script pulled from Obsidian vault session history ("one quick Claude edit I did") | 10 episodes → long-form: "I automated my [workflow]" |
| 2 | **60-Second Effect** | Short-form | Capacity-based | Screen recording, no narration, music-only | N/A (standalone shorts) |
| 3 | **Videographer's Week** | Short-form | Weekly (Friday) | Phone-at-self, "what I filmed / what I learned / what I'm testing" | 4 weeks → "Month One" long-form |
| 4 | **Month One as NYC Videographer** | Long-form | Monthly | Phone-at-self + B-roll, minimal editing | Cut DOWN into 4-6 follow-up shorts |
| 5 | **Tool Report** | Long-form primary, occasional short teaser | Bi-weekly | Review one tool (CapCut, Claude Code plugins, gear, AI editing) | Long-form base → cut into shorts |
| 6 | **BTS as Personal Videographer** | Short-form | Weekly (from Sai shoot days) | Film-style tutorial shot during/after Sai shoots | Every 10 episodes → long-form "Filming for a CEO: what I learned" |
| 7 | **Social Media Growth Update** | Short-form | Weekly | Phone-at-self, "here's my growth this week + what I tried" | Quarterly → "Growing from 0 to Xk" long-form recap |

### Cross-series rules

- **One-video-all-platforms** — every short posts to TikTok + IG Reels + YouTube Shorts
- **Bi-directional repurposing:**
  - 10 related shorts → 1 long-form compilation
  - Any standalone long-form → cut DOWN into follow-up shorts

### Removed from original

- "$X Challenge" (monthly constraint challenges) — cut for capacity reasons. Can be revisited via Pending Series Ideas if capacity opens up.

### Series Flex Rules

This series list is a living design. Expect it to change.

**Triggers that prompt a series change:**
- **Performance:** flops 3x in a row → tagged for review via Layer 7
- **Capacity:** if a series takes too long to produce AND isn't pulling weight, it gets cut or paused — no guilt
- **Trend-hop:** a trending topic/sound can spawn a TEMPORARY series (2-week duration cap) without joining the permanent list
- **Fatigue:** if Gray no longer enjoys making it, that alone is valid reason to cut — burnt-out creator > missed format

**Each series has 4 possible states:** Active / Testing / Paused / Killed

**When a series is Killed:**
- Tagged in Layer 7 registry with reason + performance data
- Never auto-suggested again by agents (see Layer 7)
- A candidate from the "Pending Series Ideas" list rotates in

**Monthly review** (last Sunday of month, 15 min):
- Check performance of every Active series
- Move stragglers to Testing or Paused
- Promote a Testing series to Active if it's earning its slot
- Pull one from Pending if a slot opens

### Pending Series Ideas

_(Empty — populated as ideas emerge. Candidates rotate in when an Active slot opens.)_

### Killed Series Archive (stub)

_(Empty — populated when a series is killed. Links to Layer 7 registry once that system exists.)_

---

## Section 3 — Distribution Simplification

Replaces the "Upload Workflow" subsection in Layer 4 (lines 232-268). Removes per-platform variant language.

### Upload Workflow

**The rule: one video, three platforms.**
- Upload order: TikTok first (primary discovery), then Instagram Reels 30-60 min later, then YouTube Shorts
- Same video file. No re-cuts. No re-renders.
- Captions CAN vary per platform (keywords shift), video CANNOT.

### Caption delta (per platform)

| Platform | Caption style | Hashtags |
|---|---|---|
| TikTok | 1-2 sentences, keywords naturally in sentence | 3-5 max |
| Instagram Reels | Slightly more personal tone | 3-5 niche + 1 trending |
| YouTube Shorts | Searchable keyword FIRST | 3-5, search-focused |

### Watermark removal

Always remove TikTok watermark before posting to IG Reels and YT Shorts. Use SnapTik or native no-watermark download.

### Long-form (YouTube)

Separate pipeline from shorts. Can be BUILT FROM shorts (compilation) or CUT INTO shorts (repurposed down). See series list long-form paths.

### X/Twitter

Text threads only. Take the video's core lesson, write as 5-tweet thread. Link the YouTube version at end. Do NOT cross-post vertical video to X.

### Removed from this section

- **Scheduling Automation** (Buffer/Later) — deferred to sub-project E (Content OS command-center tool), where it becomes `schedule_week.py`
- **Audio Strategy** — moved to Layer 1 (Research), since trending-audio monitoring is upstream of production, not distribution

---

## Section 4 — Layer 7: Iteration & Tagging System

New layer inserted after Layer 6 (Analytics and Feedback System).

### The 3-Strike Rule

Any series, format, or hook style that underperforms 3 consecutive times gets flagged for review. "Underperform" = below your rolling average on the primary metric for that format:
- Shorts: views + saves
- Long-form: watch time + subscriber conversions
- Carousels: saves + shares

3 strikes triggers a DECISION, not an auto-kill. Options:
1. **Kill it** → moves to Killed Archive, never re-suggested
2. **Pivot it** → change hook style, format, or angle (resets strike count)
3. **Keep it** → override with reason logged (e.g., "brand-building, not metrics-driven")

### Tagging Structure

Every video gets tagged at upload in the tracking system:
- Series name
- Pillar (AI+Camera, BTS, Tutorial, Before/After, Journey)
- Hook style used
- Format (talking head, screen recording, B-roll montage, etc.)
- Performance tier after 7 days: HIT / OK / MISS

Tags live in two places:
1. **Obsidian vault:** `content-os/video-log/` (one note per video, tagged with properties for search/filter)
2. **File system:** `business/social-media/video-log.csv` (flat file for Claude to query without MCP)

### Killed Archive

When a series or format is killed:
- Entry in Obsidian: `content-os/killed-archive/` with:
  - Series/format name
  - Date range it ran
  - Number of videos produced
  - Why it was killed (performance data + subjective note)
  - What replaced it
- Mirrored to: `business/social-media/killed-archive.md`

**Purpose:** agents and Claude sessions query this BEFORE suggesting new ideas. If a suggestion resembles a killed format, it gets flagged: _"This is similar to [killed format] which was cut on [date] for [reason]. Still want to try it?"_

### Winning Patterns Registry

Opposite of the Killed Archive. When something works:
- Entry in Obsidian: `content-os/winning-patterns/` with:
  - What worked (series, hook, format, topic)
  - Performance data
  - Why it worked (hypothesis)
  - How to replicate it

Agents query this to PRIORITIZE proven patterns over experiments. Target ratio: 70% proven patterns, 30% new experiments.

### Monthly Iteration Review (last Sunday, folded into Layer 6 review)

1. Check 3-strike candidates — decide: kill, pivot, or override
2. Review Killed Archive — anything worth retrying with a new angle?
3. Review Winning Patterns — are we doubling down enough?
4. Update series states: Active / Testing / Paused / Killed
5. Rotate Pending Series Ideas into open slots

---

## Section 5 — Long-Form Production Paths

New subsection added to Layer 3 (Production System).

### Two long-form flows

**Path 1: Shorts → Long-form (compilation)**
Record a mini-series of 8-12 shorts on one theme. Once complete, stitch into a single long-form with:
- New intro (30s, re-contextualize the journey)
- Original shorts as chapters (light re-edit for flow)
- New outro with takeaway + CTA

Example: 10 episodes of "Claude Edits" on editing automation → one YouTube video: "I automated my entire editing workflow"

**Path 2: Long-form → Shorts (repurpose down)**
Film a standalone long-form (Tool Report, Month One recap, etc.). After publishing, cut 4-6 highlight clips as follow-up shorts. These shorts drive traffic BACK to the long-form.

**Rule:** never film a long-form that can't produce at least 3 shorts as a byproduct. If it can't, it's too narrow.

---

## Section 6 — Sai Karra Content Pointer

One block added at the end of the Content Series section.

```markdown
### Sai Karra Content

Sai Karra has his own content playbook, strategy, and series list.
See: business/sai/content-playbook.md (sub-project B — in progress).

Graydient Media and Sai Karra content are separate brands with
separate strategies. Cross-pollination (BTS from Sai shoots for
Graydient's "BTS as Personal Videographer" series) is encouraged,
but the content calendars, analytics, and iteration systems are
independent.
```

---

## Implementation Notes

- All edits are surgical — existing sections not listed above are left untouched
- Layer/section numbering in the playbook may shift (Layer 7 is new, existing Layers 1-6 stay numbered as-is)
- The Content OS tool spec at lines 355-374 stays as-is — superseded by sub-project E
- The 12-month roadmap stays as-is — aspirational reference, not operational

---

## Content OS Master Roadmap Context

This spec (sub-project A) is one piece of a larger system:

| Sub-project | Scope | Status |
|---|---|---|
| **A — Playbook edits (Graydient)** | This spec | In progress |
| B — Sai playbook v1 | New playbook after Sai Week 1 data | Pending (week 2-4) |
| C — Iteration/vault tagging system | Build Layer 7 infrastructure in Obsidian + file system | Pending (week 1-2) |
| D — Workflow inventory + tool iteration | Rank workflows by automation-readiness, iterate content-pipeline tools | Pending (week 3-4) |
| E — Content OS command-center spec | Wrapper tool + manager-agent design | Pending (month 2) |
| F — Per-workflow skill.md builds | One agent per workflow, ongoing iteration | Pending (month 2-N) |

### Tool iteration filter (hybrid approach — Option 3)

Only iterate tools NOW if both are true:
1. Tool is actively in the content pipeline (research → script → film → edit → post → analyze)
2. Tool has a known gap or break blocking use in that flow

Tools that pass: Content Researcher, Content Pipeline, Creator Intel, Hook Optimizer, Social Media Analytics, Footage Organizer.
Tools that fail (deferred): Email Agent, Invoice System, Morning Briefing, Client Onboarding, Personal Assistant, AI Shorts Channel.

Second iteration pass happens at stage F with real production data.

### Agent evolution framework (from Personal Brand Launch / not-behind-ai-content transcript)

Each workflow follows this progression:
1. Manual (Gray does it himself)
2. Assisted (Claude helps in-session)
3. SOP (documented skill.md with exact steps)
4. Agent (skill.md runs autonomously, human reviews output)
5. Orchestrated (manager agent triggers sub-agents, human-in-loop only for creative decisions)

No workflow advances to the next stage until it performs at or above Gray's manual quality.

---

## Changelog

| Date | Version | Change |
|---|---|---|
| 2026-04-15 | 1.0 | Initial spec — all 6 sections approved in brainstorming session |
