"""
dispatcher.py
Receives a plain-text Slack message, parses the intent via brain.py,
and decides what to do: run a tool now, queue it, list queue, etc.

Returns a string — the reply to send back to Slack.
"""

import logging

from brain import parse_intent
from runner import run_tool, format_result
from task_queue import add_task, list_pending, clear_queue, format_queue_list, pending_count
from tool_registry import TOOLS, get_tool_name, help_text

log = logging.getLogger(__name__)


def handle_message(text: str) -> str:
    """
    Main entry point. Takes raw Slack message text, returns Slack reply string.
    """
    intent = parse_intent(text)
    action = intent.get("intent", "chat")
    tool_name = intent.get("tool")
    args = intent.get("args") or []
    defer = intent.get("defer", False)

    log.info(f"Intent: {action} | tool: {tool_name} | args: {args} | defer: {defer}")

    # --- HELP ---
    if action == "help":
        return help_text()

    # --- LIST QUEUE ---
    if action == "list_queue":
        return format_queue_list()

    # --- CLEAR QUEUE ---
    if action == "clear_queue":
        count = pending_count()
        if count == 0:
            return "Queue is already empty."
        clear_queue()
        return f"Queue cleared. {count} task{'s' if count > 1 else ''} cancelled."

    # --- STATUS ---
    if action == "status":
        pending = list_pending()
        lines = ["*Personal Assistant — Status*"]
        lines.append(f"• Running 24/7")
        if pending:
            lines.append(f"• Queue: {len(pending)} task(s) pending for 2am run")
            for t in pending:
                lines.append(f"  - {t['tool']}")
        else:
            lines.append("• Queue: empty")
        lines.append("\nType `help` to see all available tools.")
        return "\n".join(lines)

    # --- RUN TOOL or QUEUE TASK ---
    if action in ("run_tool", "queue_task"):
        return _handle_tool_request(tool_name, args, defer=(action == "queue_task"))

    # --- CONVERSATIONAL CHAT ---
    reply = intent.get("reply")
    if reply:
        return reply

    return ("I didn't quite catch that. Try:\n"
            "• `run social media analytics`\n"
            "• `tonight run creator intel`\n"
            "• `what's queued?`\n"
            "• `help`")


def _handle_tool_request(tool_name: str | None, args: list, defer: bool) -> str:
    """Handle a run_tool or queue_task intent."""

    # No tool identified
    if not tool_name:
        return ("I couldn't figure out which tool you meant. "
                "Type `help` to see all available tools.")

    canonical = get_tool_name(tool_name)
    if not canonical:
        return (f"I don't know a tool called '{tool_name}'. "
                "Type `help` to see what I can run.")

    tool = TOOLS[canonical]

    # Interactive tools can't run as subprocesses
    if tool["interactive"]:
        return (f"*{canonical}* uses interactive prompts, so I can't run it automatically.\n"
                f"Run it yourself in terminal:\n"
                f"`cd python-scripts/{canonical} && python main.py`")

    # Required args missing — ask before running or queuing
    if tool["required_args"] and not args:
        return (f"*{canonical}* needs an argument to run.\n"
                f"*Usage:* `{tool['args_hint']}`\n"
                f"*Example:* `{tool['example']}`")

    # --- QUEUE FOR LATER ---
    if defer:
        count = add_task(canonical, args)
        args_str = " ".join(args) if args else ""
        task_desc = f"`{canonical}" + (f" {args_str}`" if args_str else "`")
        return (f"Queued {task_desc} for tonight.\n"
                f"Total in queue: {count} task{'s' if count > 1 else ''}. I'll run them at 2am and report back.")

    # --- RUN NOW ---
    result = run_tool(canonical, args)
    return format_result(canonical, result)
