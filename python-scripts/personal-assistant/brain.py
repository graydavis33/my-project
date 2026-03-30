"""
brain.py
Uses Claude Haiku to parse a plain-English Slack message into a structured intent dict.
Called once per incoming message. Cheap + fast by design.
"""

import json
import logging
import anthropic

from config import ANTHROPIC_API_KEY
from tool_registry import TOOLS

log = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_TOOL_LIST = ", ".join(TOOLS.keys())

_SYSTEM_PROMPT = f"""You are the intent parser for a personal assistant agent.
Parse the user's message and return ONLY valid JSON — no markdown, no explanation, no extra text.

Available tools: {_TOOL_LIST}

Return this exact JSON schema:
{{
  "intent": "<one of: run_tool, queue_task, list_queue, clear_queue, status, help, chat>",
  "tool": "<tool name from the list above, or null>",
  "args": ["<cli arg 1>", "<cli arg 2>"],
  "defer": <true if user said tonight/later/overnight/when I wake up/2am, else false>,
  "reply": "<short conversational reply — ONLY for chat or help intent, otherwise null>"
}}

Intent definitions:
- run_tool    → user wants to run a specific tool RIGHT NOW
- queue_task  → user wants to run a tool later / overnight (defer=true)
- list_queue  → user asks what's in the queue (what's queued / what's running tonight)
- clear_queue → user wants to cancel/clear the queue
- status      → user asks about general project or agent status
- help        → user asks what tools are available or how to use the agent
- chat        → anything else — answer conversationally in the "reply" field

Rules:
- For queue_task: set intent=queue_task AND defer=true
- For run_tool with defer=true language: treat as queue_task
- Extract CLI args exactly as the user stated them (file paths, quoted strings, subcommands)
- If args are required but missing, still return the intent with args=[] — the dispatcher handles asking
- Pick the closest tool name match even if the user uses shorthand (e.g. "analytics" → "social-media-analytics")
- If multiple tools are mentioned in one message, return only the first one — the dispatcher will re-call for others
- Keep "reply" under 200 characters"""


def parse_intent(message: str) -> dict:
    """
    Parse a Slack message into a structured intent dict.
    Returns a safe fallback dict on any error.
    """
    try:
        response = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        )

        raw = response.content[0].text.strip()
        # Strip markdown code fences if model wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        log.debug(f"Brain raw response: {raw}")

        # Track usage for cost dashboard
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
            from usage_logger import track_response
            track_response(response)
        except Exception:
            pass

        intent = json.loads(raw)

        # Normalize: make sure all keys exist
        intent.setdefault("intent", "chat")
        intent.setdefault("tool", None)
        intent.setdefault("args", [])
        intent.setdefault("defer", False)
        intent.setdefault("reply", None)

        # If defer is true but intent is run_tool, normalize to queue_task
        if intent.get("defer") and intent.get("intent") == "run_tool":
            intent["intent"] = "queue_task"

        return intent

    except json.JSONDecodeError as e:
        log.error(f"Brain returned invalid JSON: {e}")
        return {"intent": "chat", "tool": None, "args": [], "defer": False,
                "reply": "Sorry, I had trouble understanding that. Can you rephrase?"}
    except Exception as e:
        log.exception("Brain parse_intent failed")
        return {"intent": "chat", "tool": None, "args": [], "defer": False,
                "reply": f"Something went wrong on my end: {e}"}
