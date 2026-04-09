# /save — Session End

Run this at the end of every session to log decisions, update priorities, and push everything to GitHub.

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

## Step 4: Push to GitHub

Run:
```
cd ~/Desktop/my-project && git add . && git commit -m "Session update" && git push
```

If there's nothing new to commit, skip the commit and just confirm everything is up to date.

---

## Step 5: Save Session Note to Obsidian

Using the Obsidian MCP server, write a session note to the vault at:
`~/Documents/obsidian-vault/builds/YYYY-MM-DD-session.md`

Use today's date for the filename. If a file already exists for today, append to it.

The note should include:

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
```

Keep it tight — this note is for quick recall at the start of the next session.

---

## Step 6: Confirm

Respond with a short summary:
- What was done this session (2-3 bullets max)
- Whether priorities.md was updated and what changed
- Whether any decisions were logged
- Confirm the GitHub push succeeded
- Confirm the Obsidian note was saved and where
