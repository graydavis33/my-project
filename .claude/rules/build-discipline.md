# Build Discipline

Rules to prevent the classes of problem the 2026-04-20 workspace audit exposed. These kick in BEFORE writing new code, adding new config, or shipping a new tool. Loaded every session as part of `.claude/rules/`.

Companion artifact: `audits/2026-04-20-workspace-audit.html` — re-read before any big structural change.

---

## 1. Before Building a New Python Tool

**Default answer is NO.** New projects mean new .env files, new schedulers, new README drift. The bar is high.

Checklist before proposing a new `python-scripts/` project:

- [ ] Walked `python-scripts/` and read the README of every tool whose name has any thematic overlap
- [ ] Confirmed NO existing tool does ≥50% of the proposed work
- [ ] Considered: can this live as a subcommand or flag on an existing tool?
- [ ] Considered: can this live as a shared helper in `python-scripts/shared/`?

**Extend-with-flag beats new-project.** Examples from the real audit:
- `expense-tracker` overlapped with `invoice-system` → should've been `invoice-system scan-expenses`
- `photo-organizer` overlapped with `footage-organizer` → same tool, different media type, one flag apart
- `creator-intel` overlapped with `content-researcher` → same YouTube data layer
- `screen-recording-analyzer` overlapped with `content-pipeline` → same ffmpeg + Whisper base

If the user asks for "a new tool that does X", your first question is "does any existing tool already do something adjacent?" Not "how should I architect this?"

---

## 2. Before Adding a New Skill

Skills live in `.claude/skills/`. Each has a YAML frontmatter `description` that controls when it fires.

Rules for `description`:
- **Trigger on specific contexts**, not general verbs. File paths, exact phrases, project names — good. "build", "improve", "design", "fix" — bad.
- One skill per workflow, not per tool. `invoice-expense-logger` is right because it wraps a workflow. A `video-edit-helper` skill that fires on "edit a video" is wrong — too broad, would hijack everything.
- A skill with ten action verbs and "unlimited" project types is a landmine. It will fire constantly and shadow project-specific skills.

Real cautionary tale: `ui-ux-pro-max` had 10 action verbs + unlimited project types. Zero logged invocations in 18 days (it never triggered cleanly because it always looked too generic to be right) AND would have hijacked `analytical-feature-builder`. Deleted 2026-04-20.

---

## 3. Before Adding a New MCP Server

- [ ] Have a specific use case that needs it THIS WEEK
- [ ] Not a speculative "might need later" install
- [ ] Verified there's a concrete script or workflow that will call it

Any MCP server unused for a quarter gets dropped. Real example: `magic` MCP (UI component generation) was installed, never used, and got superseded by Claude Design. Deleted 2026-04-20.

---

## 4. One Scheduler Per Job — Always

A recurring job may have exactly ONE thing scheduling it. Pick the simplest fit:

| Cadence need | Scheduler |
|---|---|
| Daemon that self-handles timing | systemd `Restart=always` (NOT cron-fired) |
| Fire once a day at a specific time | cron |
| Event-driven (on email, on file, on webhook) | event source, not a timer |

**Forbidden:** letting a script's internal scheduler run AND wiring that same script to a launchd/cron/Task Scheduler fire-every-hour. Stacks processes. Causes duplicate Slack DMs, duplicate API calls, duplicate everything.

If code changes from "one-shot script" to "long-lived daemon" or vice versa, update the schedulers in the same commit. Documented architecture must match deployed reality.

---

## 5. Doc Drift Is a Bug

When code changes, the doc updates in the same commit. No exceptions.

- Workflow SOP in `workflows/{tool}.md` matches the current commands in `main.py`
- `README.md` in the project folder matches what the tool actually does
- `CLAUDE.md` folder map + MCP table match reality (dropped servers stay dropped)
- `project-status.json` status matches `usage-stats.json` last-run data

Assume any doc older than 30 days is suspect. Read the code before trusting the doc.

Real offenders from the audit: 6 of 8 workflow docs described 1–3-version-old code. `CLAUDE.md` still listed `fetch` and `puppeteer` MCPs a week after they were dropped.

---

## 6. Config Drift Is a Worse Bug

Exactly one source of truth per concern. If two files describe the same thing:

- Eliminate one, OR
- Make one the canonical source and auto-generate the other, OR
- Add a test that fails when they disagree

Real offender from the audit: `deploy/email-agent.service` (committed) vs the inline systemd service block inside `deploy/vps-setup.sh`. They had different `Restart`, `RestartSec`, and log paths. Running `vps-setup.sh` silently overrode the committed file.

---

## 7. Claude API Calls Should Cache

Every Anthropic SDK call that's part of a multi-turn flow, a loop, or has a large shared system prompt should include `cache_control={"type": "ephemeral"}` on the cacheable parts. Single-shot one-off calls can skip this.

The workspace had zero cache usage at audit time — every prompt was paid full-price every time. Flat 50–90% savings available once caches are wired.

---

## 8. If You Change the Workspace Structure, Update CLAUDE.md

`CLAUDE.md` is the map loaded every session. Folders added, tools deleted, skills added, servers dropped — all update `CLAUDE.md` in the same commit. Otherwise next session's Claude walks into a workspace that doesn't match its own map.

Same for `context/priorities.md` when focus shifts, and `decisions/log.md` for meaningful choices.

---

## When Writing a New SOP

Use `templates/sop-template.md` as the scaffold. Keep the section order — every `workflows/*.md` shares the same shape so future Claudes (and future Gray) know where to find commands vs failure modes vs env vars without hunting. Don't invent new sections; delete ones that don't apply instead.

---

## Recurring-Audit Cadence

Run a full workspace audit roughly quarterly, or any time "things feel off." The SOP is at `workflows/workspace-audit.md` — self-contained prompts for 5 parallel research agents, verification-before-deletion discipline, branded HTML output structure. Use `audits/2026-04-20-workspace-audit.html` as the baseline for comparison. Log what changed. Delete what's dead. If a new recurring failure pattern surfaces, append it here.
