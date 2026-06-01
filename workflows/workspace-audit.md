# Workflow: Workspace Audit

**Status:** LIVE — baseline run 2026-04-20
**Cost:** ~$0.10–0.40 per run (5 parallel research agents, mostly Sonnet reads)
**Baseline:** `audits/2026-04-20-workspace-audit.html`
**Output:** `audits/{YYYY-MM-DD}-workspace-audit.html` + any companion investigation reports

---

## Objective

A top-to-bottom health check of the whole workspace. Finds dead weight, overlap between tools, stale docs, config drift, and cost-leaky patterns. Produces a branded HTML report + a prioritized action plan.

The audit is a **forcing function** — it prevents the slow accumulation of "configured but unused" sprawl that kills Claude Code workspaces over time. Every finding from the baseline run is in `build-discipline.md` as a pattern to prevent going forward.

---

## When to Run

- **Quarterly** (roughly every 3 months) as a routine health check
- **After major structural changes** — big merges, new plugin installs, deleting a bunch of tools
- **Whenever things "feel off"** — too many broken deploys, too many stale docs spotted, Claude hallucinating references to files that don't exist
- **Before onboarding anyone else** — makes the workspace legible to a second human

Always compare against the last baseline report in `audits/`. What's new? What got fixed? What recurred?

---

## What It Produces

1. **Branded HTML report** at `audits/{YYYY-MM-DD}-workspace-audit.html` — executive summary, metric cards, 5 section audits, 3-tier action plan, cut list
2. **Companion investigation reports** (optional) — any finding that needs a deep-dive lives at `audits/{YYYY-MM-DD}-{topic}-investigation.md`
3. **Decisions log entries** — one per meaningful cleanup decision
4. **New or updated rule** — if a recurring failure pattern surfaced, append to `.claude/rules/build-discipline.md`
5. **Memory update** — bump the baseline pointer in `reference_workspace_audits.md`

---

## Pre-Flight Check

Before kicking off agents:

- [ ] Read `context/priorities.md` — know what's currently in-flight (don't flag active work as "stale")
- [ ] Read the last 30 entries of `decisions/log.md` — recent decisions often look like orphans if you don't know the story
- [ ] `git log --oneline -30` — what's been touched in the last ~week
- [ ] Read the previous audit's Progress section — which recommendations from last time actually shipped vs were revised

Skipping this step is how you nearly-delete an actively-used file. See the 2026-04-20 near-miss with `screen-recording-to-sop.md`.

---

## Stage 1 — Fetch Brand Colors (for the report styling)

Read `web-apps/brand-board/color-swatches.html` before composing the report. The report uses Graydient Media's visual language — black (`#080808`), gold (`#e8b84b`), chrome, Inter font, glass cards, radial glows. Don't deviate.

If `brand-board/` has been deleted by a prior audit, the canonical palette above is enough.

---

## Stage 2 — Dispatch 5 Parallel Research Agents

Use `Agent` with `subagent_type: Explore` (read-only — they research, Claude synthesizes). All 5 fire in one message so they run concurrently.

Each prompt is self-contained (agents have no conversation context). Today's date goes into each prompt so they can compute "days since last edit" accurately.

### Agent 1 — Python Scripts

> Audit every project in `python-scripts/` for a workspace-wide consolidation report. For each subfolder: last meaningful edit vs today, entry file, .env + requirements.txt presence, API model names (Opus/Sonnet/Haiku), caching, scheduling, cross-references in dashboard.html / project-status.json / workflows/ / deploy/, recent activity in `.tmp/ results/ logs/`, overlap flags with other projects. Report each as a row with: name, days-since-activity, status (IN USE / STALE / UNUSED / NEVER CONFIGURED), cost posture (HEAVY/MODERATE/LIGHT/UNKNOWN), redundancy flag, one-line recommendation. End with top 5 consolidation wins + projects to delete outright. Research only — no file mods. Under 2000 words.

### Agent 2 — Web Apps

> Audit `web-apps/` for a consolidation report. Per subfolder: HTML entry points, last edit, links from other HTML files, backend evidence (db files, logs, recent commits), prototype vs real-app indicators, dead files (`.backup`, `.old`, `checkpoint-*`), duplicate stylesheets, GitHub Pages deployment status, relationships with `python-scripts/` siblings. Classify each as LIVE / PROTOTYPE / ABANDONED / REFERENCE-ONLY. End with consolidation + deletion recommendations. Research only. Under 1500 words.

### Agent 3 — Claude Config + MCPs

> Audit `.claude/` in the project and `~/.claude.json` + `~/.claude/settings.json` in user scope. Enumerate slash commands (usage counts if available), rules files, custom skills (including SKILL.md frontmatter trigger-quality rating), hooks, MCP servers (classify as ACTIVE/DORMANT based on whether scripts or workflows reference them), installed plugins. Cross-check against `CLAUDE.md` — flag anything listed there that no longer exists, or anything present that's undocumented. Report top 5 consolidation recommendations. Research only. Under 1500 words.

### Agent 4 — Documentation Layer

> Audit `context/`, `workflows/`, `plans/`, `decisions/log.md`, `docs/`, `references/`, `templates/`, `business/`, and root .md files. For each layer: file count, stale/orphaned files (>30 days no edit + no recent cross-reference), duplicates, specific deletion candidates. For `plans/`: classify each plan as IMPLEMENTED / PARTIALLY IMPLEMENTED / GHOST (never executed) / SUPERSEDED by comparing to current code + decisions/log.md + recent commits. For `workflows/`: cross-check each SOP against the actual `python-scripts/{tool}/main.py` and flag drift. Research only. Under 2000 words.

### Agent 5 — Root + Deploy

> Audit repo root + `deploy/` + anything that doesn't fit other sections. Per file: purpose, last edit, cross-references, liveness (dashboard serving real data? sync script running? services actually installed?). Specifically verify: dashboard.html matches what's deployed at graydavis33.github.io/my-project/dashboard.html, sync_usage.py produces usage-stats.json on schedule, tiktok-callback.html wired to OAuth flow, deploy/.service files match committed vs inline-in-vps-setup.sh versions. Flag orphans + config drift. Research only. Under 1200 words.

---

## Stage 3 — Verification Before Deletion

**Critical step — skip this and you'll nearly-delete something active.**

For every file or folder an agent flagged for deletion:

1. **Grep the repo** for references to the name. `workflows/{name}.md`, `context/priorities.md`, `decisions/log.md`, `dashboard.html` — all common cross-ref sites.
2. **Check `decisions/log.md` for mentions in the last 30 days.** If it was recently built or recently discussed, it's probably not dead.
3. **Check `context/priorities.md`.** If it's in the active priority list, DON'T flag for deletion even if it looks stale.
4. **Ask Gray if unsure.** The cost of asking is low; the cost of deleting his in-flight work is high.

Real lesson from 2026-04-20: `workflows/screen-recording-to-sop.md` was flagged as an orphan. It was actually built that same day and was the on-ramp for Sai's podcast workflow. Checking `decisions/log.md` would have caught it. I didn't, Gray did.

---

## Stage 4 — Synthesize the Report

Single-file HTML at `audits/{YYYY-MM-DD}-workspace-audit.html`. Structure:

- **Hero** — Graydient Media wordmark + gradient title + date + agent count
- **Progress section** (if this isn't the first audit) — what shipped since last baseline, what got revised, what's still pending
- **Executive summary** — glass card with gold border, 2-3 paragraphs on top-level findings
- **Metric row** — 6 counter cards (Python count, web-app count, live %, stale docs, hard deletes, credit spend)
- **Five section pages** — one per agent's scope, with status-coded tables
- **Action plan** — three-column grid: Immediate (this week) / Short-term (2 weeks) / Compound (ongoing)
- **Cut list** — single block of confirmed-dead files/folders with one-line reasons
- **Footer** — Graydient Media wordmark + date

Styling constants — copy from the 2026-04-20 baseline:
- Font: Inter 300-900
- Palette: `--gold: #e8b84b`, `--ice: #38BDF8`, `--black: #080808`, status colors (`--ok: #4ADE80`, `--warn: #FBBF24`, `--bad: #F87171`)
- Glass cards with 1px border, 18px radius, backdrop blur
- Badges for status, tags for cost posture
- Sticky TOC nav at top

Keep the report as one self-contained HTML file — no external dependencies besides the Google Fonts import for Inter.

---

## Stage 5 — Post-Audit Discipline

After the report lands:

1. **Append to `decisions/log.md`** — one entry per meaningful decision made during cleanup
2. **Update `context/priorities.md`** — only if priorities actually shifted
3. **Update `build-discipline.md`** — if a recurring failure pattern surfaced that isn't already covered, add a section
4. **Update `reference_workspace_audits.md`** in auto-memory — bump the baseline pointer to the new file path
5. **Optionally update CLAUDE.md** — if workspace shape changed (tools deleted, folders reorganized, MCPs dropped)

---

## Stage 6 — Execute in Tiers (Don't Freelance Destructive Work)

Present the action plan to Gray. Group by risk:

- **Tier 0 — Pure text fixes** — doc polish, rule updates. Autonomous OK.
- **Tier 1 — Confirmed-dead deletions** — items with strong cross-reference evidence they're unused. Ask Gray for one green light, then batch.
- **Tier 2 — Tool merges, model downgrades** — behavior changes. Each needs a `/create-plan`.
- **Tier 3 — VPS / live services / shared infra** — highest risk. Deliberate pace, verify after each change.

Never execute Tier 2+ without an explicit sign-off. "The audit said so" is not sign-off — Gray reads every recommendation with the judgment the agents don't have.

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| Agent returns truncated results | Shrink scope — split Python audit by subfolder, or run a focused re-audit just for that area |
| Conflicting findings between agents | Trust the one closest to the source of truth (code > docs > memory > intuition). Flag conflicts in the report for Gray to resolve. |
| Nearly-deleted something active | Add the specific cross-reference check that would have caught it to the "Verification Before Deletion" step above. Audit the pre-flight discipline, not just the workspace. |
| Audit report HTML doesn't match brand | Re-read `brand-board/color-swatches.html` (or use the hardcoded palette in Stage 2). Never improvise colors. |
| Report is too long to be useful | Trim section-page tables to top 15 rows. Deeper detail belongs in companion investigation reports, not the main HTML. |

---

## Cadence

Aim for **quarterly**. Reminder belongs on the calendar, not in a memory file. If more than 6 months passes between audits, the gap itself is a finding for the next one.
