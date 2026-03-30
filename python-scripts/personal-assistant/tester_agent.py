"""
tester_agent.py
Runs a tool and uses Claude Sonnet to analyze the output.
Returns a Slack-ready PASS/FAIL verdict with plain-English explanation.

Pure function — no conversation history needed.
"""

import logging
import anthropic

from config import ANTHROPIC_API_KEY
from runner import run_tool
from tool_registry import get_tool_name

log = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM_PROMPT = """\
You are a QA engineer reviewing the output of an automation tool.
Given the tool name, args, stdout, stderr, and exit code — analyze whether it worked correctly.

Your response format (always follow this exactly):
1. First line: "PASS" or "FAIL" (just the word, bold it with *PASS* or *FAIL*)
2. 2-3 sentence summary of what the tool did or tried to do
3. If FAIL: specific error, likely cause, and what needs to be fixed
4. If PASS: note any warnings or unusual output worth flagging (or "No issues." if clean)

Keep the total response under 250 words. This goes directly to Slack — no markdown headers, \
no bullet walls. Write like a senior engineer giving a quick verbal status."""


def test_tool(tool_name: str, args: list) -> str:
    """
    Run tool_name with args, analyze the output with Claude Sonnet,
    and return a Slack-formatted PASS/FAIL verdict string.
    """
    canonical = get_tool_name(tool_name)
    if not canonical:
        return f"*FAIL* — Unknown tool `{tool_name}`. Type `help` to see available tools."

    log.info(f"Tester: running {canonical} {args}")
    result = run_tool(canonical, args)

    # Build analysis prompt
    args_str = " ".join(args) if args else "(none)"
    stdout_snippet = result["stdout"][:3000] if result["stdout"] else "(no output)"
    stderr_snippet = result["stderr"][:1000] if result["stderr"] else "(none)"

    user_prompt = f"""Tool: {canonical}
Args: {args_str}
Exit code: {result["returncode"]}
Stdout:
{stdout_snippet}
{"(output truncated)" if result.get("truncated") else ""}
Stderr:
{stderr_snippet}"""

    try:
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Track usage
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
            from usage_logger import track_response
            track_response(response)
        except Exception:
            pass

        analysis = response.content[0].text.strip()
        return f"*Test: {canonical}*\n\n{analysis}"

    except Exception as e:
        log.exception("Tester agent Claude call failed")
        # Fall back to raw result summary
        icon = "✅" if result["success"] else "❌"
        status = "Exit 0" if result["success"] else f"Exit {result['returncode']}"
        fallback = f"{icon} *Test: {canonical}* — {status} (analysis unavailable: {e})"
        if result["stderr"]:
            fallback += f"\n`{result['stderr'][:300]}`"
        return fallback
