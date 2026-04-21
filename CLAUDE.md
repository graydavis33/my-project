# Claude — Gray's Workspace

You are Gray Davis's AI operator and executive assistant. Read context files to understand who Gray is and what he's working toward.

---

## Context

@context/me.md
@context/work.md
@context/priorities.md
@context/goals.md

---

## How This Workspace Works

**Folder map:**
- `context/` — who Gray is, his business, priorities, Q2 goals, Sai Karra job
- `workflows/` — SOPs for each automation tool. Read before working on any project.
- `plans/` — dated implementation plans. Created by /create-plan, executed by /implement.
- `decisions/log.md` — append-only log of meaningful decisions, never delete entries
- `python-scripts/` — 14 automation tools (one folder per project)
- `web-apps/` — HTML/CSS/JS tools (Analytical SaaS, Payday Checklist, Brand Board, etc.)
- `business/` — contracts, leads, reference docs (Sai job notes)
- `deploy/` — VPS deployment: vps-setup.sh + 3 .service files for systemd
- `references/` — source library: framework docs and templates studied to build this workspace
- `templates/` — reusable templates (currently session-summary.md)
- `.claude/commands/` — slash commands: /prime, /create-plan, /implement, /save
- `.claude/rules/` — behavior rules loaded every session (communication, code, habits)
- `.claude/skills/` — custom skills (3 active — see below)

**Root files:**
- `dashboard.html` — project status dashboard, served at graydavis33.github.io/my-project/dashboard.html
- `sync_usage.py` + `usage-stats.json` + `project-status.json` — dashboard data layer
- `tiktok-callback.html` — TikTok OAuth redirect (URL hardcoded in TikTok dev console, must stay at root)

---

## Session Commands

- `/prime` — run at session start. Loads context, checks recent commits, briefs on priorities.
- `/create-plan [request]` — plan before building anything non-trivial. Writes a dated doc to `plans/`.
- `/implement [plan-path]` — executes a plan step by step with validation.
- `/save` — session end: commits + pushes + updates dashboard.

---

## Planning Workflow Selection

**Claude decides which planning approach to use, not Gray.** Heuristics:
- 1–3 files, clear scope, no architecture → `/create-plan` (or no plan if truly trivial)
- Multi-file, multi-project, or touches live cloud tools → `superpowers:writing-plans`
- Goal is fuzzy ("I want X to be better") → `superpowers:brainstorming` first
- One-line fixes, config tweaks, doc updates, questions → no plan

Always announce the choice when starting work. Gray can override.

---

## Installed Plugins

Three Claude Code plugins enabled in `~/.claude/settings.json`:

- **superpowers** — TDD, debugging, brainstorming, planning, parallel agents, code review, verification-before-completion. Use the relevant skill via the Skill tool before non-trivial work.
- **claude-md-management** — audits and improves CLAUDE.md files in the workspace.
- **skill-creator** — builds new skills into `.claude/skills/`.

---

## Custom Skills

Three custom skills live in `.claude/skills/`:

- **google-oauth-refresh** — re-auth flow for when token.json expires (7-day testing-mode expiry). Triggers on 401s / RefreshError.
- **invoice-expense-logger** — workflow for `python-scripts/invoice-system/main.py` (scan-receipts, scan-payments, add-expense, import-csv, create-invoice).
- **analytical-feature-builder** — house style for Analytical SaaS (Chart.js + barGlow plugin, --accent-rgb theming, glass variants, preview-real.html prototype-first).

Each skill = a folder with a SKILL.md file (YAML frontmatter + instructions). Build new ones as recurring workflows emerge.

---

## Cloud Deployment (VPS)

Three tools run 24/7 on a Hostinger VPS (`72.61.10.152`) without your local machine being on:

- **email-agent** — systemd daemon (`Restart=always`). The Python script handles its own internal 7am–8pm hourly cadence via the `schedule` library. Do NOT also schedule this via cron, launchd, or Task Scheduler — stacking schedulers spawns duplicate daemons. One canonical runner (VPS), period.
- **morning-briefing** — cron job at 8am daily (installed by `deploy/vps-setup.sh`)
- **invoice-system** — cron job at 9am daily, runs `scan-all`

VPS deployment files live in `deploy/`. Re-deploy from scratch: `bash deploy/vps-setup.sh` (run from local). Note: `vps-setup.sh` writes its own inline email-agent systemd service — it does NOT use the committed `deploy/email-agent.service` file. If you edit one, verify the other.

---

## MCP Servers

Six MCP servers configured in `~/.claude.json` (VS Code extension uses `--strict-mcp-config` and reads this file, not `settings.json`):

| Server | Purpose |
|---|---|
| filesystem | Access to `C:/Users/Gray Davis/my-project` and `G:/` (project scope) |
| github | GitHub repo access via GITHUB_TOKEN |
| gdrive | Google Drive access |
| obsidian | Read/write to `Obsidian/Graydient Media` vault |
| slack | Slack workspace access (bot token + team ID) |
| sequential-thinking | Structured multi-step reasoning |

---

## Core Rules

**Before building:** Check `workflows/` for an existing SOP. Check `python-scripts/` for existing tools. Use the planning heuristics above.

**When something breaks:** Read the full error → fix the script → verify → update the workflow with what was learned. Ask before re-running paid API calls.

**Security:** `.env`, `token.json`, `client_secret*.json`, `credentials.json` are always gitignored. API keys live in `.env` only, never hardcoded.

**GitHub:** `https://github.com/graydavis33/my-project`. Auto-commit + auto-push happen on `Stop` and `PreCompact` hooks (configured in `~/.claude/settings.json`).

---

## Maintenance

- Update `context/priorities.md` when focus shifts
- Update `context/goals.md` at the start of each quarter
- Update `workflows/` when a script fails and something new is learned
- Update `decisions/log.md` when a significant choice is made
- Update `dashboard.html` and `project-status.json` when project statuses change
- After any structural change to this workspace, update this file
