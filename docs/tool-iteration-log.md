# Tool Iteration Log

Running log of the "apply the AI-workflow-video framework to each existing tool, one at a time" effort.

**Framework source:** `python-scripts/content-pipeline/output/not-behind-ai-content-transcript-20260414-112732.md`

**Approach types:**
- **A — Fix the brain:** master prompt + Role-Context-Command-Format formula on existing prompts
- **B — Add feedback loop:** capture rejections/edits, feed back into prompts/profile
- **C — Skill-file refactor:** move prompts out of code into `.claude/skills/<tool>/SKILL.md`

---

## Status

| # | Tool | Status | Date | Approach | Design doc | Notes |
|---|---|---|---|---|---|---|
| 1 | Email Agent | In progress | 2026-04-14 | A | [2026-04-14-email-agent-fix-the-brain-design.md](superpowers/specs/2026-04-14-email-agent-fix-the-brain-design.md) | Design approved, plan pending |
| 2 | Invoice System | Pending | — | — | — | — |
| 3 | Morning Briefing | Pending | — | — | — | — |
| 4 | Social Media Analytics | Pending | — | — | — | — |
| 5 | Hook Optimizer | Pending | — | — | — | — |
| 6 | Content Researcher | Pending | — | — | — | — |
| 7 | Content Pipeline | Pending | — | — | — | — |
| 8 | Client Onboarding | Pending | — | — | — | — |
| 9 | Creator Intel | Pending | — | — | — | — |
| 10 | Footage Organizer | Pending | — | — | — | — |
| 11 | Personal Assistant | Pending | — | — | — | — |
| 12 | AI Shorts Channel | Pending | — | — | — | — |
| 13 | Expense Tracker | Pending | — | — | — | — |
| 14 | Photo Organizer | Pending | — | — | — | — |

**Status values:** Pending, In progress, Done, Skipped

---

## Iteration history

### 2026-04-14 — Email Agent, Approach A
- Started: 2026-04-14
- Design doc: [2026-04-14-email-agent-fix-the-brain-design.md](superpowers/specs/2026-04-14-email-agent-fix-the-brain-design.md)
- Goal: shared `role_context.md` master prompt + rewrite classifier/drafter prompts using Role-Context-Command-Format formula
- Outcome: TBD

**RESUME POINT (2026-04-14, end of session):**
- Design approved by Gray, all 4 sections
- Design doc + this log + memory pointer written
- Implementation plan NOT yet written (writing-plans skill not invoked)
- **Next action when resuming:**
  1. Gray answers Mac-vs-VPS deployment question (recommendation: VPS authoritative, disable Mac launchd)
  2. I draft a first-pass `role_context.md` based on workspace context files + what I know about Sai + Gray reviews/edits
  3. Then invoke `superpowers:writing-plans` to generate the step-by-step implementation plan
- Transcript that kicked this off: `python-scripts/content-pipeline/output/not-behind-ai-content-transcript-20260414-112732.md`
