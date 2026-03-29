# Framework Reference Catalog

Everything in this folder is source material for building Gray's master Claude Code framework.
Use this as the map before implementing anything.

---

## Files at a Glance

```
json/
├── CATALOG.md                          ← This file
├── CLAUDE.md                           ← Nate's WAT framework (source)
├── executive-assistant-init-prompt.md  ← Liam's EA onboarding prompt (source)
└── trigger-dev/
    ├── mcp.json                        ← Trigger.dev MCP server config
    └── trigger-ref.md                  ← Trigger.dev SDK v4 API reference
└── claude-workspace-template/
    └── claude-workspace-template/
        ├── CLAUDE.md                   ← Liam's workspace template main file
        ├── shell-aliases.md            ← cs / cr shell aliases for session launch
        ├── context/
        │   ├── personal-info.md        ← Template: who you are
        │   ├── business-info.md        ← Template: your business
        │   ├── strategy.md             ← Template: current strategic priorities
        │   └── current-data.md         ← Template: live metrics / KPIs
        └── .claude/
            ├── commands/
            │   ├── prime.md            ← /prime command: session initialization
            │   ├── create-plan.md      ← /create-plan command: plan before building
            │   └── implement.md        ← /implement command: execute a plan
            └── skills/
                ├── skill-creator/
                │   └── SKILL.md        ← How to build skills (meta-skill)
                └── mcp-integration/
                    └── SKILL.md        ← MCP server integration patterns
```

---

## What Each Source Contributes

### Nate Herk — WAT Framework (`CLAUDE.md`)
**Philosophy:** AI orchestrates, Python executes. Keeps accuracy high across multi-step tasks.

Key ideas to steal:
- `workflows/` folder — markdown SOPs per task/project. Written like you're briefing a teammate.
- `tools/` folder — reusable Python scripts for deterministic execution
- `.tmp/` folder — temp/intermediate files, always disposable
- **Self-improvement loop:** fail → fix tool → verify → update workflow → move on
- Rule: check `tools/` before building anything new
- Rule: if an API call costs money, ask before retrying

---

### Liam Ottley — Workspace Template (`claude-workspace-template/`)
**Philosophy:** Structured workspace + session commands + skills = assistant that gets smarter over time.

Key ideas to steal:

#### Folder Structure
- `context/` — 4 files that load who you are, your business, your strategy, your current metrics
- `plans/` — dated implementation plan files (`2026-03-29-add-feature.md`)
- `outputs/` — deliverables and work products
- `reference/` — templates, examples, reusable patterns
- `decisions/log.md` — append-only decision log

#### Slash Commands (`.claude/commands/`)
- `/prime` — runs at session start; reads CLAUDE.md + context/, summarizes understanding, confirms ready
- `/create-plan [request]` — research workspace → write detailed plan doc to `plans/` → ask user before implementing
- `/implement [plan-path]` — read plan → execute step-by-step → validate → mark as Implemented

#### Skills System (`.claude/skills/`)
- Each skill = a folder with `SKILL.md` (YAML frontmatter + instructions)
- YAML frontmatter `description` is what triggers the skill automatically
- Skills can include `scripts/`, `references/`, `assets/` subfolders
- Progressive disclosure: frontmatter always loaded, SKILL.md body loaded on trigger, references loaded as needed
- Build organically — don't pre-create skills, let recurring workflows reveal what needs one

#### Shell Aliases
- `cs` — launch Claude + auto-run `/prime` (safe mode, asks permission)
- `cr` — launch Claude + auto-run `/prime` (run mode, skips permission prompts)

#### CLAUDE.md Rules
- Keep UNDER 150 lines
- Use `@context/me.md` imports instead of repeating content
- Claude must update CLAUDE.md whenever workspace structure changes
- Rule files go in `.claude/rules/` (one topic per file, max 3-4 to start)

---

### Liam Ottley — EA Init Prompt (`executive-assistant-init-prompt.md`)
**What it is:** A one-time initialization prompt. Run it in a fresh project to scaffold the full
executive assistant folder structure and populate all context files via a 6-section onboarding interview.

Folder structure it creates:
```
CLAUDE.md, CLAUDE.local.md, .gitignore
.claude/settings.json, rules/, skills/
context/me.md, work.md, team.md, current-priorities.md, goals.md
templates/session-summary.md
references/sops/, references/examples/
projects/
decisions/log.md
archives/
```

When to use: If we ever want to do a clean-slate setup or onboard a new project from scratch.
For Gray's existing setup, we adapt the structure rather than running this verbatim.

Notable additions over the workspace template:
- `CLAUDE.local.md` — git-ignored personal overrides (great for local secrets/preferences)
- `decisions/log.md` — append-only decision history
- `archives/` folder — never delete, archive instead
- `templates/session-summary.md` — end-of-session closeout template
- `.claude/rules/` — rule files separated by topic (not crammed into CLAUDE.md)
- Section 6 answers become a "Skills to Build" backlog

---

### Trigger.dev (`trigger-dev/`)
**What it is:** A background job and task queue platform. Runs TypeScript/JavaScript tasks on schedules
or triggers — think "GitHub Actions but for code, with retries, waits, and orchestration built in."

**MCP server:** `trigger-dev/mcp.json` — adds Trigger.dev as an MCP tool in Claude Code.
Add to `~/.claude/settings.json` mcpServers to enable.

**Key patterns from the API reference:**
- `task()` — basic background task with retry config
- `schedules.task()` — cron-scheduled task (replaces Windows Task Scheduler / GitHub Actions)
- `schemaTask()` — typed task with Zod validation
- `triggerAndWait()` — parent/child task orchestration
- Idempotency keys — prevent duplicate processing when polling feeds
- `wait.for()` / `wait.until()` — pause tasks without consuming compute
- **Orchestrator + Processor pattern** — scheduler polls for new items, hands each off to a processor task

**Relevance to Gray:**
- Could replace Windows Task Scheduler for Social Media Analytics, Morning Briefing, Creator Intel
- Orchestrator + Processor is exactly how Content Pipeline should work at scale
- Would need a Trigger.dev account and TypeScript rewrite of Python scripts — medium effort

---

## Implementation Priority (What to Build First)

| # | What | From | Effort | Impact |
|---|------|------|--------|--------|
| 1 | `/prime` command | Liam | Low | High — session context every time |
| 2 | `/create-plan` + `/implement` | Liam | Low | High — plan-then-execute discipline |
| 3 | `context/` folder (pre-filled for Gray) | Liam | Low | High — lean CLAUDE.md, rich context |
| 4 | `workflows/` folder with SOPs | Nate | Medium | High — tells me HOW to run each project |
| 5 | `decisions/log.md` | Liam/EA | Low | Medium — decision history |
| 6 | `CLAUDE.local.md` + `.claude/rules/` | Liam/EA | Low | Medium — clean separation |
| 7 | `templates/session-summary.md` | Liam/EA | Low | Medium — structured closeouts |
| 8 | Skills (build organically) | Liam | Ongoing | High long-term |
| 9 | Trigger.dev integration | Nate/Trigger | High | High long-term (scheduling upgrade) |
