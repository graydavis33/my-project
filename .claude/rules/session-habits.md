# Session Habits

Rules for how to behave across every session.

---

## Session Start

- Run /prime at the start of every session to load full context
- Check context/priorities.md — always know what the top 3 priorities are
- Suggest what to work on if Gray doesn't have a specific request

## Before Building Anything Non-Trivial

- Check workflows/ for an existing SOP before writing new code
- Check python-scripts/ for existing tools that already do part of the job
- For anything touching multiple files or adding new features: use /create-plan first

## Self-Improvement Loop (from Nate's WAT framework)

When something breaks:
1. Read the full error — don't guess
2. Fix the script
3. Verify the fix works before moving on
4. Update the relevant workflow in workflows/ with what was learned
5. If it was a paid API call that failed, ask before re-running

## During Work

- Complete one thing fully before moving to the next
- If blocked and can't move forward — ask, don't guess
- Flag anything that looks like a security risk immediately

## Session End

- Auto-push to GitHub: `cd ~/Desktop/my-project && git add . && git commit -m "Session update" && git push`
- Update context/priorities.md if anything changed
- Log any meaningful decisions in decisions/log.md

## Dashboard

- File: dashboard.html in repo root
- URL: https://graydavis33.github.io/my-project/dashboard.html
- Update at start/end of sessions when project statuses change
