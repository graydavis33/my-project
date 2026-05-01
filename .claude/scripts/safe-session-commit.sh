#!/usr/bin/env bash
# Safe Session Commit — replaces the bare `git add . && git commit && git push`
# Stop / PreCompact hook. Aborts if the auto-commit would silently push a
# large deletion (the failure mode that wiped 3,217 lines on 2026-05-01).
#
# Triggers:
#   - >= 5 files deleted, OR
#   - >= 200 lines deleted
#
# On trigger: leaves changes UNSTAGED in the working tree (no commit, no
# push) and appends a row to .claude/auto-commit-skipped.log so the next
# session sees the warning. Investigate manually before the next push.

set -uo pipefail

REPO="c:/Users/Gray Davis/my-project"
cd "$REPO" || exit 0

# Nothing tracked-modified or untracked? exit silently.
if [ -z "$(git status --porcelain)" ]; then
    exit 0
fi

git add .

# How much would this commit delete?
DELETED_FILES=$(git diff --cached --diff-filter=D --name-only | wc -l | tr -d ' ')
DELETED_LINES=$(git diff --cached --numstat | awk '{sum += $2} END {print sum + 0}')

THRESHOLD_FILES=5
THRESHOLD_LINES=200

if [ "$DELETED_FILES" -ge "$THRESHOLD_FILES" ] || [ "$DELETED_LINES" -ge "$THRESHOLD_LINES" ]; then
    git reset HEAD . >/dev/null 2>&1
    LOG="$REPO/.claude/auto-commit-skipped.log"
    {
        echo "---"
        echo "$(date -Iseconds) — auto-commit BLOCKED"
        echo "deleted_files=$DELETED_FILES deleted_lines=$DELETED_LINES"
        echo "thresholds: files>=$THRESHOLD_FILES OR lines>=$THRESHOLD_LINES"
        echo "files affected:"
        git status --porcelain
    } >> "$LOG"
    echo "[safe-session-commit] BLOCKED: $DELETED_FILES files / $DELETED_LINES lines would be deleted." >&2
    echo "[safe-session-commit] Changes left unstaged. See .claude/auto-commit-skipped.log" >&2
    exit 0
fi

git commit -m "Session update" >/dev/null 2>&1
git push >/dev/null 2>&1 || true
exit 0
