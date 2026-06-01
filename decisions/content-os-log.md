# Content OS — Decision Log

Append-only log of meaningful decisions for the Content OS initiative (sub-projects A → F). Separated from `decisions/log.md` to prevent Content OS noise from drowning the main decision log.

Format: `YYYY-MM-DD — [sub-project] — decision — reason`

---

## 2026-04-15 — [A, C, D, E, F] — Content OS master roadmap approved

Six sub-projects defined:
- A — Playbook edits (Graydient)
- B — Sai playbook v1
- C — Iteration/vault tagging system
- D — Workflow inventory + tool iteration
- E — Content OS command-center spec
- F — Per-workflow skill.md builds

Reason: single playbook overhaul was too big to ship as one unit. Splitting into surgical sub-projects lets each ship independently and get real-world tested before the next one builds on it.

Spec: `docs/superpowers/specs/2026-04-15-content-playbook-edits-design.md`

## 2026-04-15 — [A] — All 6 edit sections approved in brainstorming

Section 1 (Capacity & Constraints), 2 (Series list 5→7), 3 (Distribution simplification), 4 (Layer 7), 5 (Long-form paths), 6 (Sai pointer) — all greenlit.

## 2026-04-15 — [A] — Killed "$X Challenge" series

Reason: capacity. Monthly constraint challenges require too much production overhead for current 5-10h/week ceiling. Can be revisited via Pending Series Ideas if capacity opens up.

## 2026-04-15 — [A] — One-video-all-platforms rule

Reason: per-platform re-cuts doubled production time without proportional engagement gain. Same video, three uploads. Captions vary, video doesn't.

## 2026-04-15 — [A] — Audio Strategy moved from Layer 4 to Layer 1

Reason: trending audio drives WHAT gets made (pacing, edit style, topic), not HOW it gets distributed. Belongs upstream in Research, not downstream in Distribution.

## 2026-04-15 — [A] — Scheduling Automation deferred to sub-project E

Reason: Buffer/`schedule_week.py` integration is a tooling concern, not a playbook concern. Lives inside the Content OS command-center (sub-project E) when it ships month 2.

## 2026-04-15 — [D] — Hybrid tool iteration filter (Option 3)

Only iterate a tool NOW if BOTH are true:
1. Tool is actively in the content pipeline
2. Tool has a known gap or break blocking use in that flow

Pass: Content Researcher, Content Pipeline, Creator Intel, Hook Optimizer, Social Media Analytics, Footage Organizer.
Fail (deferred): Email Agent, Invoice System, Morning Briefing, Client Onboarding, Personal Assistant, AI Shorts Channel.

Reason: iterating all 14 tools up front would burn capacity on tools that don't block the content pipeline. Second pass happens at stage F with real production data.

## 2026-04-15 — [F] — Agent Evolution Framework adopted

Every workflow progresses: Manual → Assisted → SOP → Agent → Orchestrated.

Rule: no workflow advances until it performs at or above Gray's manual quality. No jumping to "Agent" because the SOP was written — the SOP has to run reliably at quality first.

Source: Personal Brand Launch / not-behind-ai-content transcript.

## 2026-04-21 — [A] — Sub-project A shipped

All 6 edit sections applied to `business/social-media/content-playbook.md`:
- Capacity & Constraints inserted after The Big Picture
- Content Series expanded 5 → 7, "$X Challenge" removed, Flex Rules + Pending/Killed stubs added
- Long-Form Production Paths added to Layer 3
- Layer 4 Distribution simplified to one-video-all-platforms rule
- Audio Strategy moved to Layer 1
- Layer 7 (Iteration & Tagging) inserted
- Sai Karra content pointer added

## 2026-04-21 — [C] — Sub-project C file-system half shipped

`business/social-media/video-log.csv`, `killed-archive.md`, and `winning-patterns.md` scaffolded with schemas and stub entries. Obsidian vault half (video-log/, killed-archive/, winning-patterns/ folders) still pending — requires in-vault work in a separate session.
