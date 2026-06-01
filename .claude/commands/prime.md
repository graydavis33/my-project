# /prime — Session Initialization

Run this at the start of every session to load full context and orient for the work ahead.

---

## Step 1: Read Context

Read the following files in order:
- `CLAUDE.md`
- `context/me.md`
- `context/work.md`
- `context/priorities.md`
- `context/goals.md`

---

## Step 2: Check What's New

Run: `git log --oneline -5`

This shows the last 5 commits — what was built or changed in recent sessions.

---

## Step 3: Deliver Session Briefing

Provide a structured briefing in this format:

---

**Who I'm working with:**
One sentence — Gray's role, business, and current focus.

**Where we left off:**
Based on recent git commits and context files — what was last worked on.

**Current top priorities:**
Pull the top 3 from `context/priorities.md`. For each: project name, status, and next action.

**Q2 Goals check-in:**
Which of the Q2 goals from `context/goals.md` are most relevant to today's session.

**My suggestion for today:**
Based on priorities and momentum, recommend the single best thing to work on this session and why.

**Top 3 MCP servers to add:**
Based on what's being worked on this session and Gray's current toolset, recommend the 3 most useful MCP servers he doesn't already have connected. For each: server name, what it does, and why it's relevant right now.

**Ready to work.** Confirm and ask: "What do you want to tackle?"

---

## Notes

- Keep the briefing tight — no walls of text
- If context files are stale or something seems off, flag it
- Always end with a concrete suggestion, not just a summary