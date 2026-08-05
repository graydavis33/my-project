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
- `business/monetization/PIPELINE.md`

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

**Monetization Watch:**
From `business/monetization/PIPELINE.md` — read-only, no subagent, no analysis. 3–6 lines:
- The NOW candidate + its next action and your recommended course of action (or "quiet — still watching")
- Anything added to WATCHLIST/RADAR since the previous session (use the entries' added-dates)
- Any ideas KILLED since the previous session — named, with the reason (Gray can pull any back up)
If the pipeline is empty and backfill is pending, say so in one line.

**Top 3 MCP servers to add:**
Based on what's being worked on this session and Gray's current toolset, recommend the 3 most useful MCP servers he doesn't already have connected. For each: server name, what it does, and why it's relevant right now.

Then go to **Step 4** — the daily schedule check-in (but read its ONCE-PER-DAY gate first; most later-in-the-day sessions skip it).

---

## Step 4: Daily Schedule Check-In → Work Calendar

### ⛔ ONCE PER DAY — check this BEFORE asking anything

The check-in runs **at most once per calendar day**, not once per session. Gray often runs several sessions a day and does not want to be re-asked.

**Gate:** if `python-scripts/calendar-blocker/days/<today>.json` already exists, today is already blocked out → **do NOT ask the questions.** Say one line ("today's already blocked out — skipping the check-in") and go straight to "What do you want to tackle?".

Only run the check-in when that file is missing. If Gray explicitly asks to redo or change today's schedule, re-run it on request — write the updated file, then `clear` + `block` today (idempotent).

---

Every morning, after the briefing, ask Gray a short set of questions about **today**, then turn his answers into time blocks on his **gray@karramedia.com** Work calendar (the "Work — Gray (Schedule)" calendar he shares with Sai). This saves him from entering it by hand. The cadence is different every day, so ask fresh every time — never assume yesterday's schedule.

### Ask this (one compact list, he answers inline)

Present it as a single block so he can rip through it fast. Tell him rough is fine ("10–12", "after class ~2pm", "skip") and that you'll read the blocks back after.

1. **Headline** — the one main thing today is about?
2. **Top priorities / finishing** — the 1–3 things that have to move today?
3. 🎓 **Class** — start–end time? (or none)
4. 🎬 **Filming** — time + who/what? (or none)
5. 💻 **Editing / content work** — which time blocks?
6. 🏋️ **Workout** — time?
7. 🍽 **Meals** — lunch time? (and dinner if it's fixed)
8. 📞 **Anything else on a set time** — meetings, calls, appointments, errands?

Adapt the list to what's going on — drop questions that clearly don't apply, add one if the briefing surfaced something time-bound. Keep it to a quick-answer list, not a back-and-forth.

### Turn answers into blocks

- Map each timed answer to a block. If he gives a start only, infer a sensible duration (workout ~1h, lunch ~45m, meals/calls as stated) — but if something's genuinely ambiguous, ask one quick clarifier rather than guess wildly.
- Times are **NYC / America/New_York** (already set in the tool's config).
- Skip any item he answered "none" / "skip". If there are **no** timed items at all, don't write to the calendar — just note his priorities and move on.
- Use a consistent color per block type so his calendar reads at a glance:

| Block | Emoji | colorId |
|---|---|---|
| Filming | 🎬 | 11 (Tomato) |
| Editing / deep work / long-form | 💻 | 9 (Blueberry) |
| Class | 🎓 | 3 (Grape) |
| Workout | 🏋️ | 10 (Basil) |
| Meals (lunch/dinner) | 🍽 | 5 (Banana) |
| Meetings / calls | 📞 | 7 (Peacock) |
| Post / deliverable | 📌 | 6 (Tangerine) |

### Write it (calendar-blocker tool)

Build today's block file, then clear-today-and-block so re-runs never duplicate:

```
# Write python-scripts/calendar-blocker/days/YYYY-MM-DD.json:
# { "date": "YYYY-MM-DD", "blocks": [
#     {"start": "HH:MM", "end": "HH:MM", "title": "🎬 Filming — ...", "desc": "...", "color": 11}, ... ] }

python python-scripts/calendar-blocker/gcal.py clear YYYY-MM-DD
python python-scripts/calendar-blocker/gcal.py block python-scripts/calendar-blocker/days/YYYY-MM-DD.json
```

Then read the blocks back to Gray (time – time – title) and confirm they landed.

**Guardrail:** in this check-in, `clear`/`block` only ever touch **today's** date. Never clear a past day or any other day — see `feedback-calendar-never-clear-past-days`. The clear is scoped to today's Work-calendar blocks (it's a dedicated calendar), so it's safe to re-run when he re-answers.

**Ready to work.** Confirm and ask: "What do you want to tackle?"

---

## Notes

- Keep the briefing tight — no walls of text
- If context files are stale or something seems off, flag it
- Always end with a concrete suggestion, not just a summary