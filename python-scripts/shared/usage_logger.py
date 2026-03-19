"""
usage_logger.py
Shared module — logs run timestamps and Claude API cost to ~/.my-project-usage.json.

Usage (add to the top of any live script's main function):
    from shared.usage_logger import log_run
    log_run("your-project-name")

Then add track_response() after every client.messages.create() call:
    from shared.usage_logger import track_response
    response = client.messages.create(...)
    track_response(response)

The log file lives at ~/.my-project-usage.json and is NEVER committed to git.
sync_usage.py runs automatically in the background when any script exits — dashboard
updates ~60s later. Type `usage` anytime to force an immediate manual sync.

Pricing ($/1M tokens) — update if Anthropic changes rates: console.anthropic.com
"""
import atexit
import json
import os
import subprocess
import sys
from datetime import datetime, timezone


_LOG_PATH = os.path.expanduser("~/.my-project-usage.json")

# Path to sync_usage.py — 3 levels up from this file (shared/ → python-scripts/ → repo root)
_SYNC_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "sync_usage.py"
)

# Pricing per 1 million tokens (input_rate, output_rate)
_PRICING = {
    "claude-haiku":  (0.80,  4.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-opus":  (15.00, 75.00),
}

_current_project = None
_accum = {"tokens_in": 0, "tokens_out": 0, "model": None}
_atexit_registered = False


def _compute_cost(tokens_in: int, tokens_out: int, model: str) -> float:
    """Return estimated cost in USD given token counts and model name."""
    in_rate, out_rate = 3.00, 15.00  # default to Sonnet pricing
    if model:
        model_lower = model.lower()
        for key, rates in _PRICING.items():
            if key in model_lower:
                in_rate, out_rate = rates
                break
    return round((tokens_in * in_rate + tokens_out * out_rate) / 1_000_000, 6)


def _flush_cost() -> None:
    """Write accumulated token/cost entry to the log. Called on exit or before next run."""
    global _current_project, _accum
    if not _current_project or (_accum["tokens_in"] == 0 and _accum["tokens_out"] == 0):
        return
    try:
        entries = []
        if os.path.exists(_LOG_PATH):
            with open(_LOG_PATH, "r", encoding="utf-8") as f:
                entries = json.load(f)
        entries.append({
            "project":    _current_project,
            "ts":         datetime.now(timezone.utc).isoformat(),
            "tokens_in":  _accum["tokens_in"],
            "tokens_out": _accum["tokens_out"],
            "cost_usd":   _compute_cost(_accum["tokens_in"], _accum["tokens_out"], _accum["model"]),
        })
        with open(_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f)
        # Spawn sync in background — dashboard updates ~60s later without manual `usage` command
        if os.path.exists(_SYNC_SCRIPT):
            subprocess.Popen(
                [sys.executable, _SYNC_SCRIPT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass


def log_run(project: str) -> None:
    """Append a timestamped run entry for `project`. Silently no-ops on any error."""
    global _current_project, _accum, _atexit_registered
    try:
        # Flush any accumulated cost from a previous run before resetting
        if _current_project and (_accum["tokens_in"] > 0 or _accum["tokens_out"] > 0):
            _flush_cost()

        _current_project = project
        _accum = {"tokens_in": 0, "tokens_out": 0, "model": None}

        if not _atexit_registered:
            atexit.register(_flush_cost)
            _atexit_registered = True

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


def track_response(response, model: str = None) -> None:
    """Call immediately after any client.messages.create() to accumulate token usage."""
    global _accum
    try:
        _accum["tokens_in"]  += response.usage.input_tokens
        _accum["tokens_out"] += response.usage.output_tokens
        if not _accum["model"]:
            _accum["model"] = model or getattr(response, "model", None)
    except Exception:
        pass
