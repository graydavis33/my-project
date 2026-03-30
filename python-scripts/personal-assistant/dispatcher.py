"""
dispatcher.py
Agentic loop: receives a Slack message + channel ID, runs the commander,
executes any tool calls Claude makes, feeds results back, and returns the final reply.
"""

import logging

import commander
import tester_agent
from runner import run_tool, format_result
from task_queue import add_task, list_pending, clear_queue, format_queue_list, pending_count
from tool_registry import get_tool_name, TOOLS

log = logging.getLogger(__name__)

_MAX_TOOL_ITERATIONS = 5  # safety cap — prevents infinite tool-call loops


def handle_message(text: str, channel: str) -> str:
    """
    Main entry point. Takes raw Slack message + channel ID, returns reply string.
    """
    response = commander.think(channel, text)
    commander.record_assistant_response(channel, response)

    iterations = 0

    while response.stop_reason == "tool_use" and iterations < _MAX_TOOL_ITERATIONS:
        iterations += 1

        # Execute every tool_use block in this response
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_result = _execute_tool(block.name, block.input)
            log.info(f"Tool '{block.name}' executed. result_len={len(tool_result)}")

            commander.add_tool_result(channel, block.id, block.name, tool_result)

        # Ask Claude to continue now that it has tool results
        response = commander.think(channel, "")
        commander.record_assistant_response(channel, response)

    if iterations >= _MAX_TOOL_ITERATIONS:
        log.warning("Hit max tool iterations — returning partial response")

    # Extract final text reply
    reply = _extract_text(response)
    return reply


# ── Tool execution ────────────────────────────────────────────────────────────

def _execute_tool(tool_name: str, inputs: dict) -> str:
    """Execute a tool call from Claude and return a plain-text result string."""

    if tool_name == "run_tool":
        return _do_run_tool(inputs.get("tool_name", ""), inputs.get("args") or [])

    if tool_name == "test_tool":
        return tester_agent.test_tool(
            inputs.get("tool_name", ""),
            inputs.get("args") or [],
        )

    if tool_name == "queue_task":
        return _do_queue_task(
            inputs.get("tool_name", ""),
            inputs.get("args") or [],
            inputs.get("note", ""),
        )

    if tool_name == "list_queue":
        return format_queue_list()

    if tool_name == "clear_queue":
        count = pending_count()
        if count == 0:
            return "Queue is already empty."
        clear_queue()
        return f"Queue cleared. {count} task{'s' if count > 1 else ''} cancelled."

    if tool_name == "get_status":
        return _do_get_status()

    return f"Unknown tool: '{tool_name}'"


def _do_run_tool(tool_name: str, args: list) -> str:
    if not tool_name:
        return "No tool name provided."

    canonical = get_tool_name(tool_name)
    if not canonical:
        return f"Unknown tool '{tool_name}'. Available: {', '.join(TOOLS.keys())}"

    tool = TOOLS[canonical]
    if tool["interactive"]:
        return (
            f"{canonical} uses interactive prompts and can't run automatically. "
            f"Run it yourself: cd python-scripts/{canonical} && python main.py"
        )

    result = run_tool(canonical, args)
    return format_result(canonical, result)


def _do_queue_task(tool_name: str, args: list, note: str) -> str:
    if not tool_name:
        return "No tool name provided to queue."

    canonical = get_tool_name(tool_name)
    if not canonical:
        return f"Unknown tool '{tool_name}'."

    count = add_task(canonical, args, note)
    args_str = (" " + " ".join(args)) if args else ""
    return (
        f"Queued `{canonical}{args_str}` for the 2am overnight run. "
        f"Total in queue: {count} task{'s' if count > 1 else ''}."
    )


def _do_get_status() -> str:
    pending = list_pending()
    lines = ["Personal Assistant is running 24/7."]
    if pending:
        lines.append(f"Queue: {len(pending)} task(s) pending for 2am run:")
        for t in pending:
            lines.append(f"  - {t['tool']}")
    else:
        lines.append("Queue: empty")
    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_text(response) -> str:
    """Pull plain text out of a Claude response. Falls back gracefully."""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            return block.text.strip()
    return "Done."
