"""
tool_registry.py
Single source of truth for all tools the Personal Assistant can run.

Each entry:
  description   — shown in "help" response
  path          — absolute path to the tool folder (relative to PA_SCRIPTS_BASE)
  cmd           — command list after "python" (usually just ["main.py"])
  args_hint     — shown when Gray asks how to use the tool
  required_args — True = dispatcher asks for args before running (can't run with nothing)
  interactive   — True = uses input(), cannot run as subprocess (tell Gray to run manually)
"""

import os
from config import PA_SCRIPTS_BASE


def _tool_path(folder: str) -> str:
    return os.path.join(PA_SCRIPTS_BASE, folder)


TOOLS: dict[str, dict] = {
    "hook-optimizer": {
        "description": "Generate YouTube titles, hooks, and thumbnail concepts for a video idea",
        "path": _tool_path("hook-optimizer"),
        "cmd": ["main.py"],
        "args_hint": "your video concept in quotes",
        "example": 'hook-optimizer "how I edit a wedding film in one hour"',
        "required_args": True,
        "interactive": False,
    },
    "content-researcher": {
        "description": "Research a video concept — finds outlier YouTube videos + full Claude analysis",
        "path": _tool_path("content-researcher"),
        "cmd": ["main.py"],
        "args_hint": "your video concept in quotes",
        "example": 'content-researcher "drone cinematography tips"',
        "required_args": True,
        "interactive": False,
    },
    "content-pipeline": {
        "description": "Transcribe a video file and find the best short-form clips using Claude",
        "path": _tool_path("content-pipeline"),
        "cmd": ["main.py"],
        "args_hint": "absolute path to your video file",
        "example": "content-pipeline /path/to/video.mp4",
        "required_args": True,
        "interactive": False,
    },
    "invoice-system": {
        "description": "Scan Gmail for income/receipts/payments and update your finances spreadsheet",
        "path": _tool_path("invoice-system"),
        "cmd": ["main.py"],
        "args_hint": "subcommand: scan-all, scan-receipts, scan-payments, or create-invoice",
        "example": "invoice-system scan-all",
        "required_args": True,
        "interactive": False,
    },
    "social-media-analytics": {
        "description": "Fetch analytics from YouTube, TikTok, Instagram, Facebook → Google Sheets",
        "path": _tool_path("social-media-analytics"),
        "cmd": ["-X", "utf8", "main.py"],
        "args_hint": "no args needed",
        "example": "social-media-analytics",
        "required_args": False,
        "interactive": False,
    },
    "morning-briefing": {
        "description": "Send the daily morning briefing to Slack right now",
        "path": _tool_path("morning-briefing"),
        "cmd": ["main.py"],
        "args_hint": "no args needed",
        "example": "morning-briefing",
        "required_args": False,
        "interactive": False,
    },
    "client-crm": {
        "description": "Manage your client pipeline: list, add, update stage, send weekly reminder",
        "path": _tool_path("client-crm"),
        "cmd": ["main.py"],
        "args_hint": "subcommand: list, add, remind, or update <id> <stage>",
        "example": "client-crm list",
        "required_args": True,
        "interactive": False,
    },
    "client-onboarding": {
        "description": "Full client onboarding: intake → brief → contract PDF → email → Sheets",
        "path": _tool_path("client-onboarding"),
        "cmd": ["main.py"],
        "args_hint": "no args — but must be run in your terminal (uses interactive prompts)",
        "example": "client-onboarding",
        "required_args": False,
        "interactive": True,  # uses input() — cannot run as subprocess
    },
    "creator-intel": {
        "description": "Fetch and analyze latest videos from your monitored YouTube creators",
        "path": _tool_path("creator-intel"),
        "cmd": ["main.py"],
        "args_hint": "no args needed",
        "example": "creator-intel",
        "required_args": False,
        "interactive": False,
    },
    "footage-organizer": {
        "description": "Organize raw video footage by type (broll, interview, action...) using Claude Vision",
        "path": _tool_path("footage-organizer"),
        "cmd": ["main.py"],
        "args_hint": "absolute path to your footage folder",
        "example": "footage-organizer /path/to/footage/",
        "required_args": True,
        "interactive": False,
    },
}


def get_tool(name: str) -> dict | None:
    """Return tool config by exact name, or fuzzy-match a close name."""
    if name in TOOLS:
        return TOOLS[name]
    # Try partial match (e.g. "analytics" → "social-media-analytics")
    name_lower = name.lower()
    for key in TOOLS:
        if name_lower in key or key in name_lower:
            return TOOLS[key]
    return None


def get_tool_name(name: str) -> str | None:
    """Return the canonical tool key for a fuzzy name, or None."""
    if name in TOOLS:
        return name
    name_lower = name.lower()
    for key in TOOLS:
        if name_lower in key or key in name_lower:
            return key
    return None


def help_text() -> str:
    """Return a formatted list of all tools for the 'help' Slack response."""
    lines = ["*Here's everything I can run for you:*\n"]
    for name, tool in TOOLS.items():
        tag = " _(run in terminal)_" if tool["interactive"] else ""
        lines.append(f"• *{name}*{tag} — {tool['description']}")
        lines.append(f"  Example: `{tool['example']}`")
    lines.append("\nJust tell me what to do in plain English. "
                 "Add 'tonight' or 'later' to queue it for the overnight run (2am).")
    return "\n".join(lines)
