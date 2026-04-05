#!/usr/bin/env python3
"""
Saves a session log to Obsidian vault at the end of each Claude Code session.
Runs automatically via Stop hook in ~/.claude/settings.json
"""

import os
import subprocess
from datetime import datetime

VAULT_PATH = os.path.expanduser("~/Documents/obsidian-vault")
SESSIONS_FOLDER = os.path.join(VAULT_PATH, "Claude Sessions")
PROJECT_PATH = os.path.expanduser("~/Desktop/my-project")


def run_git(args):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_recent_commits():
    out = run_git(["log", "--oneline", "-5"])
    return out or "No recent commits"


def get_changed_files():
    out = run_git(["diff", "--name-only", "HEAD~1", "HEAD"])
    if not out:
        out = run_git(["diff", "--name-only", "--cached"])
    return out or "No files changed"


def main():
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    filename = f"Session {date_str}.md"
    filepath = os.path.join(SESSIONS_FOLDER, filename)

    os.makedirs(SESSIONS_FOLDER, exist_ok=True)

    recent_commits = get_recent_commits()
    changed_files = get_changed_files()

    session_block = f"""
---

## Session ended at {time_str}

**Recent commits:**
```
{recent_commits}
```

**Files changed in last commit:**
```
{changed_files}
```

**Notes:**
_(add notes here)_
"""

    if os.path.exists(filepath):
        # Append to today's existing note
        with open(filepath, "a") as f:
            f.write(session_block)
    else:
        # Create new note for today
        content = f"""---
date: {date_str}
type: claude-session-log
tags: [claude, sessions]
---

# Claude Session Log — {date_str}
{session_block}"""
        with open(filepath, "w") as f:
            f.write(content)


if __name__ == "__main__":
    main()
