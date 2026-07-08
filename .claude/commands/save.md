# /save — Session End

Run this at the end of every session to log decisions, update priorities, save a session note to Obsidian, and push everything to GitHub.

---

## Step 1: Review What Happened This Session

Look back at the conversation — what was built, changed, decided, or learned?

---

## Step 2: Update `context/priorities.md`

Read the current `context/priorities.md`.

If any project status changed this session (something got built, unblocked, or deprioritized), update the relevant row in the Active Priority List. Update the `_Last updated` date at the top.

If nothing changed, leave the file alone.

---

## Step 3: Log Decisions in `decisions/log.md`

If any meaningful decision was made this session — a choice about architecture, tooling, direction, or approach that would be worth remembering — append it to `decisions/log.md` using this format:

```
[YYYY-MM-DD] DECISION: ... | REASONING: ... | CONTEXT: ...
```

Only log decisions that are non-obvious or wouldn't be clear from reading the code. Skip logging small implementation details.

If no meaningful decisions were made, skip this step.

---

## Step 4: Save Session Note to Obsidian Vault

Using the **Write tool** (not MCP — the obsidian MCP server is not loading reliably), save a session note to:

```
C:/Users/Gray Davis/Documents/Obsidian/Graydient Media/Sessions/YYYY-MM-DD-session.md
```

Use today's date (UTC) for the filename. If a file already exists for today, read it first and append a new section dated with the current time, instead of overwriting.

Format:

```markdown
# Session — YYYY-MM-DD

## What Was Built / Changed
- [bullet per thing done]

## Decisions Made
- [any decisions logged, or "None"]

## Blockers / Pending
- [anything left unfinished or waiting on Gray]

## Next Actions
- [what to pick up next session]

## Related
- [[Home]]
- Project: [[<related project name if applicable>]]
```

Use `[[wikilinks]]` for any project names, decisions, or context files mentioned. This makes the Obsidian graph view connect this session to related notes.

Keep it tight — this note is for quick recall at the start of the next session.

---

## Step 5: Run the Monetization Strategist

Spawn the `monetization-strategist` subagent (Agent tool). If that subagent type isn't available in this session (fresh registry), spawn `general-purpose` instead with this prefix: `You are the monetization-strategist. Read ".claude/agents/monetization-strategist.md" and follow it exactly as your instructions for this input:`

Prompt (fill the placeholders):

```
Daily run. Session date: <YYYY-MM-DD>.
SESSION SUMMARY:
<the session-note content you just wrote in Step 4>
FILES CHANGED THIS SESSION:
<file paths changed this session — from the session's commits (git log) or git status; write "none" if none>
DISCUSSION-ONLY SIGNALS: <1-3 bullets of monetization-relevant things that were TALKED about but left no file trace, or "none">
```

It updates `business/monetization/PIPELINE.md` + `state.json` and returns a short report — include that report in the Step 7 confirmation. **Never let this step block the save:** if the strategist errors or hangs, note it and continue to Step 6 — the cursor didn't move, so the missed delta is analyzed automatically next session.

---

## Step 6: Push to GitHub

The Stop hook in `~/.claude/settings.json` auto-commits + pushes when Claude stops responding. So normally this step is automatic.

If for some reason auto-push didn't fire (e.g., hooks were disabled, or you want an explicit message), manually run:

```bash
cd "C:/Users/Gray Davis/my-project" && git add . && git commit -m "Session update: <one-line summary>" && git push
```

---

## Step 7: Confirm

Respond with a short summary:
- What was done this session (2-3 bullets max)
- Whether priorities.md was updated and what changed
- Whether any decisions were logged
- The path of the Obsidian session note
- The monetization-strategist's report (or "strategist skipped/errored" if it didn't run)
- Confirm GitHub state (auto-pushed or manual)
