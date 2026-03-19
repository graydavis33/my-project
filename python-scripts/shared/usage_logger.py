"""
usage_logger.py
Shared module — logs a run timestamp to ~/.my-project-usage.json.

Usage (add these 2 lines near the top of any live script's main function):
    from shared.usage_logger import log_run
    log_run("your-project-name")

The log file lives at ~/.my-project-usage.json and is NEVER committed to git.
Run sync_usage.py at the repo root to compute stats and push to the dashboard.
"""
import json
import os
from datetime import datetime, timezone


_LOG_PATH = os.path.expanduser("~/.my-project-usage.json")


def log_run(project: str) -> None:
    """Append a timestamped run entry for `project`. Silently no-ops on any error."""
    try:
        entries = []
        if os.path.exists(_LOG_PATH):
            with open(_LOG_PATH, "r", encoding="utf-8") as f:
                entries = json.load(f)
        entries.append({
            "project": project,
            "ts": datetime.now(timezone.utc).isoformat()
        })
        with open(_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f)
    except Exception:
        pass  # Never crash a live script over logging
