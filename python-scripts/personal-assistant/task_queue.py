"""
task_queue.py
JSON-backed task queue for overnight / deferred tool runs.
All reads and writes go through this module — no other file touches task_queue.json directly.
"""

import json
import os
import time
import logging

log = logging.getLogger(__name__)

_QUEUE_FILE = os.path.join(os.path.dirname(__file__), "task_queue.json")


def _load() -> list:
    if not os.path.exists(_QUEUE_FILE):
        return []
    try:
        with open(_QUEUE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        log.warning("Could not read task_queue.json — starting with empty queue")
        return []


def _save(tasks: list):
    with open(_QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


def add_task(tool: str, args: list, note: str = "") -> int:
    """Add a pending task to the queue. Returns the new queue length."""
    tasks = _load()
    tasks.append({
        "tool": tool,
        "args": args,
        "note": note,
        "queued_at": time.time(),
        "status": "pending",
    })
    _save(tasks)
    log.info(f"Queued task: {tool} {args}")
    return len([t for t in tasks if t["status"] == "pending"])


def pop_all_pending() -> list:
    """
    Return all pending tasks and mark them as 'running'.
    Called by the scheduler at 2am before executing the queue.
    """
    tasks = _load()
    pending = [t for t in tasks if t["status"] == "pending"]
    for t in tasks:
        if t["status"] == "pending":
            t["status"] = "running"
    _save(tasks)
    return pending


def mark_done(tool: str, success: bool):
    """Mark the most recent 'running' task for this tool as done or failed."""
    tasks = _load()
    for t in reversed(tasks):
        if t["tool"] == tool and t["status"] == "running":
            t["status"] = "done" if success else "failed"
            t["finished_at"] = time.time()
            break
    _save(tasks)


def list_pending() -> list:
    """Return all tasks still waiting to run."""
    return [t for t in _load() if t["status"] == "pending"]


def clear_queue():
    """Remove all pending tasks (leaves done/failed history intact)."""
    tasks = _load()
    for t in tasks:
        if t["status"] == "pending":
            t["status"] = "cancelled"
    _save(tasks)
    log.info("Queue cleared.")


def pending_count() -> int:
    return len(list_pending())


def format_queue_list() -> str:
    """Return a Slack-ready string listing pending tasks."""
    pending = list_pending()
    if not pending:
        return "Queue is empty — nothing scheduled for tonight."
    lines = [f"*Queue ({len(pending)} task{'s' if len(pending) > 1 else ''} pending — runs at 2am):*"]
    for i, t in enumerate(pending, 1):
        args_str = " ".join(t["args"]) if t["args"] else ""
        note = f" _{t['note']}_" if t.get("note") else ""
        lines.append(f"{i}. *{t['tool']}*{' `' + args_str + '`' if args_str else ''}{note}")
    return "\n".join(lines)
