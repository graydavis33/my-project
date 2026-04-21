# Tool Inventory — Agent Evolution Stages

Ranks every tool in the workspace against the Agent Evolution Framework. Source: sub-project D of Content OS roadmap.

## The Framework (5 stages)

1. **Manual** — Gray does it himself, start to finish
2. **Assisted** — Claude helps in-session (pair programming / review)
3. **SOP** — documented `skill.md` with exact steps; anyone (or any AI) can follow
4. **Agent** — the `skill.md` runs autonomously, Gray reviews the output
5. **Orchestrated** — a manager agent triggers sub-agents; human-in-loop only for creative decisions

**Advancement rule:** no workflow advances to the next stage until it performs at or above Gray's manual quality.

## Hybrid iteration filter

A tool gets iterated NOW only if BOTH are true:
1. Actively used in the content pipeline (research → script → film → edit → post → analyze)
2. Has a known gap or break blocking that flow

---

## Rankings

### Passes hybrid filter (iterate now — Priority tier)

| Tool | Current stage | Target stage | Known gap blocking advance | Next action |
|---|---|---|---|---|
| **Content Researcher** | Assisted | Agent | No daily trend brief; docs reference old 5-step pipeline but actual code is agentic. Reddit layer exists but isn't wired into an automated output. | Build `daily_trend_brief()` that runs cached-daily, DMs Slack with 3 topic recs. Update workflow doc to match actual code. |
| **Content Pipeline** | Assisted | SOP | Lacks `export_all_formats.py` (title suggestions, captions, X thread, YT description). Drafts folder convention not codified. | Add `export_all_formats.py`. Write `skill.md` for the end-to-end video → drafts flow. |
| **Creator Intel** | Assisted | Agent | No Sunday Slack outlier report. Creators list not pinned. | Build `weekly_outlier_report.py`. Hard-code 7 tracked creators in config. |
| **Hook Optimizer** | SOP | Agent | Runs on-demand only. No batch mode to score a week of hook candidates at once. | Add batch CLI + Slack integration. Output scored JSON. |
| **Social Media Analytics** | Agent | Orchestrated | All 4 platforms live. Next: feed data into Analytical SaaS backend. | Wire Playwright scraper output into Analytical backend (not Graph API). |
| **Footage Organizer** | Agent | Agent (stable) | Test-set.csv from real misses not built yet. April 16 misc/ folder needs manual re-sort. | Build eval.py test set → tighten prompt → release v2. |

### Fails hybrid filter (deferred — Stage F revisit with production data)

| Tool | Current stage | Why deferred |
|---|---|---|
| **Email Agent** | Agent | Already in Fix-the-Brain iteration (see `tool-iteration-log.md`). Not part of content pipeline. |
| **Invoice System** | SOP | Finance tool, not content pipeline. `invoice-expense-logger` skill already exists. |
| **Morning Briefing** | Agent | Runs daily via VPS. Not blocking content flow. |
| **Client Onboarding** | SOP | Low-frequency use, not blocking. |
| **Personal Assistant** | Assisted | Experimental commander; not a production content tool. |
| **AI Shorts Channel** | SOP | Separate pipeline — AI news shorts, not Graydient content. Awaiting accounts + .env. |
| **Expense Tracker** | (folded into Invoice System) | Not a separate tool. |
| **Photo Organizer** | Not built | Not a current priority. |

### Web apps / other (not ranked — not "tools" in the agent sense)

- Analytical SaaS — a product, not a personal workflow tool
- Payday Checklist — user-facing app, not an agent
- Brand Board — static reference page

---

## Iteration order (priority tier)

Based on what unblocks the most downstream content work:

1. **Content Researcher** — upstream of everything. Fix first so trend briefs start flowing.
2. **Hook Optimizer** — batch mode unblocks the research-to-script handoff.
3. **Content Pipeline** — `export_all_formats.py` unblocks the produce-to-publish handoff.
4. **Creator Intel** — weekly outlier report feeds back into research + hook bank.
5. **Social Media Analytics → Analytical** — closes the feedback loop for Layer 6 (Analytics) + Layer 7 (Iteration).
6. **Footage Organizer** — stable; polish via test-set eval once upstream flows are moving.

---

## Advancement checklist (per tool)

Before declaring a tool "advanced" to the next stage, verify:

- [ ] `skill.md` exists and is accurate
- [ ] Tool has been run end-to-end 3 times at current stage with Gray's approval
- [ ] Output quality matches or beats Gray's manual baseline
- [ ] Failure modes documented (what breaks it, what to do when it breaks)
- [ ] Logged to `decisions/content-os-log.md` with the date of advancement

---

_Last updated: 2026-04-21 (sub-project D initial draft)_
