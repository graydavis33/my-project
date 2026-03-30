"""
commander.py
Claude Sonnet executive assistant with tool_use + per-session conversation history.
Replaces brain.py entirely.

think(channel_id, user_text)  →  raw Anthropic response object
  - If response contains tool_use blocks, dispatcher executes them and calls think() again
  - If response is text only, dispatcher returns the reply to Slack
"""

import logging
import anthropic

from config import ANTHROPIC_API_KEY
from tool_registry import TOOLS

log = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Per-channel conversation history: { channel_id: [{"role": ..., "content": ...}, ...] }
_sessions: dict[str, list] = {}

_MAX_TURNS = 20  # max messages to keep per session before pruning


# ── Tool schema Claude can call ───────────────────────────────────────────────

def _build_tool_list_description() -> str:
    lines = []
    for name, tool in TOOLS.items():
        tag = " (must be run manually — interactive)" if tool["interactive"] else ""
        lines.append(f"  • {name}{tag}: {tool['description']}")
    return "\n".join(lines)


COMMANDER_TOOLS = [
    {
        "name": "run_tool",
        "description": (
            "Run one of Gray's automation tools right now and return the output. "
            "Use this when Gray wants to execute a tool immediately."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool to run (e.g. 'social-media-analytics', 'creator-intel')",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CLI arguments for the tool (e.g. a video path, a concept string, a subcommand)",
                },
            },
            "required": ["tool_name"],
        },
    },
    {
        "name": "test_tool",
        "description": (
            "Run a tool and get a QA analysis of the output — returns PASS or FAIL "
            "with a plain-English explanation. Use this when Gray wants to test or validate a tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool to test",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CLI arguments for the tool",
                },
            },
            "required": ["tool_name"],
        },
    },
    {
        "name": "queue_task",
        "description": (
            "Queue a tool to run overnight at 2am. Use this when Gray says 'tonight', "
            "'later', 'overnight', 'when I wake up', or otherwise defers a task."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool to queue",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CLI arguments for the tool",
                },
                "note": {
                    "type": "string",
                    "description": "Optional note about why this was queued",
                },
            },
            "required": ["tool_name"],
        },
    },
    {
        "name": "list_queue",
        "description": "Show what tasks are currently in the overnight queue.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "clear_queue",
        "description": "Clear all pending overnight tasks from the queue.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_status",
        "description": "Show the agent's current status: is it running, what's in the queue, etc.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


def _system_prompt() -> str:
    tools_list = _build_tool_list_description()
    return f"""You are Gray's executive assistant — smart, direct, and efficient. \
You operate via Slack, so Gray reads your replies on his phone. Keep it concise.

Gray is a freelance videographer and AI operator building automation tools under his brand \
Graydient Media. He's focused on building, testing, and deploying his 12 automation tools.

Your capabilities:
- Run any of his tools right now (run_tool)
- Test a tool and report whether it worked (test_tool)
- Queue tools to run overnight at 2am (queue_task)
- Check or manage the overnight queue (list_queue, clear_queue)
- Report agent status (get_status)
- Answer questions, give suggestions, and reason through problems (just reply — no tool needed)

Rules:
- When Gray asks a general question or wants advice → just answer, no tool
- When Gray wants a tool run immediately → use run_tool
- When Gray wants something tested/validated → use test_tool
- When Gray says "tonight", "later", "overnight", "queue it" → use queue_task
- If a tool requires args (like a file path or concept) and Gray didn't provide them → ask before running
- Interactive tools (client-onboarding) can't be run automatically — tell Gray to run them in terminal

Gray's tools:
{tools_list}

Current priorities (for when Gray asks what to work on):
1. Content Pipeline — test with a real video file end-to-end
2. Content Researcher V2 — add Reddit layer
3. Client CRM — run setup and configure Google Sheet
"""


# ── Session management ────────────────────────────────────────────────────────

def _get_history(channel_id: str) -> list:
    return _sessions.setdefault(channel_id, [])


def _prune_history(channel_id: str):
    history = _sessions.get(channel_id, [])
    if len(history) > _MAX_TURNS:
        _sessions[channel_id] = history[-_MAX_TURNS:]


# ── Public API ────────────────────────────────────────────────────────────────

def think(channel_id: str, user_text: str) -> object:
    """
    Add user_text to history (if non-empty) and call Claude Sonnet.
    Returns the raw Anthropic response — may contain tool_use blocks.
    Dispatcher calls this, handles tool execution, then calls think() again with empty text.
    """
    history = _get_history(channel_id)

    if user_text:
        history.append({"role": "user", "content": user_text})

    log.info(f"Commander thinking. channel={channel_id} history_len={len(history)}")

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_system_prompt(),
        tools=COMMANDER_TOOLS,
        messages=history,
    )

    log.info(f"Commander stop_reason={response.stop_reason} blocks={len(response.content)}")

    # Track usage
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
        from usage_logger import track_response
        track_response(response)
    except Exception:
        pass

    return response


def add_tool_result(channel_id: str, tool_use_id: str, tool_name: str, result_text: str):
    """
    After dispatcher executes a tool, call this to record the assistant's tool_use
    block and the tool_result back into history so Claude has full context.
    """
    history = _get_history(channel_id)

    # The assistant message with the tool_use block must already be in history
    # (added by record_assistant_response). We just add the tool_result user turn.
    history.append({
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result_text,
            }
        ],
    })
    _prune_history(channel_id)


def record_assistant_response(channel_id: str, response):
    """
    Record Claude's raw response (which may have tool_use blocks) into history.
    Must be called before add_tool_result so the assistant turn is in place.
    """
    history = _get_history(channel_id)
    history.append({"role": "assistant", "content": response.content})
    _prune_history(channel_id)


def add_final_reply(channel_id: str, reply_text: str):
    """
    Record the final plain-text reply from Claude into history.
    Called after the agentic loop resolves.
    """
    history = _get_history(channel_id)
    # If last message is already assistant (from record_assistant_response), skip re-adding
    if history and history[-1]["role"] == "assistant":
        return
    history.append({"role": "assistant", "content": reply_text})
    _prune_history(channel_id)
