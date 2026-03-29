"""
runner.py
Spawns any registered tool as a subprocess and captures its output.
"""

import subprocess
import sys
import logging

from tool_registry import TOOLS, get_tool_name
from config import PA_MAX_OUTPUT_CHARS

log = logging.getLogger(__name__)

# Max time (seconds) to wait for a tool to finish before killing it
_TIMEOUT = 600


def run_tool(tool_name: str, extra_args: list[str]) -> dict:
    """
    Run a tool by name as a subprocess.

    Returns:
      {
        "success":    bool,
        "stdout":     str,
        "stderr":     str,
        "returncode": int,
        "truncated":  bool   # True if output was cut to PA_MAX_OUTPUT_CHARS
      }
    """
    canonical = get_tool_name(tool_name)
    if not canonical:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Unknown tool: '{tool_name}'. Type 'help' to see what I can run.",
            "returncode": -1,
            "truncated": False,
        }

    tool = TOOLS[canonical]

    # Build the command: [this python] [tool flags] main.py [extra args]
    # tool["cmd"] is e.g. ["main.py"] or ["-X", "utf8", "main.py"]
    cmd = [sys.executable] + tool["cmd"] + extra_args

    log.info(f"Running tool '{canonical}': {' '.join(cmd)} (cwd={tool['path']})")

    try:
        result = subprocess.run(
            cmd,
            cwd=tool["path"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
            encoding="utf-8",
            errors="replace",
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        truncated = False

        if len(stdout) > PA_MAX_OUTPUT_CHARS:
            stdout = stdout[:PA_MAX_OUTPUT_CHARS]
            truncated = True

        log.info(f"Tool '{canonical}' finished. returncode={result.returncode}")
        if result.returncode != 0:
            log.warning(f"Tool '{canonical}' stderr: {stderr[:500]}")

        return {
            "success": result.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": result.returncode,
            "truncated": truncated,
        }

    except subprocess.TimeoutExpired:
        log.error(f"Tool '{canonical}' timed out after {_TIMEOUT}s")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Timed out after {_TIMEOUT}s. The tool may still be running in the background.",
            "returncode": -1,
            "truncated": False,
        }
    except Exception as e:
        log.exception(f"Tool '{canonical}' failed with exception")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "truncated": False,
        }


def format_result(tool_name: str, result: dict) -> str:
    """Turn a run_tool() result into a Slack-ready message string."""
    icon = "✅" if result["success"] else "❌"
    status = "Done" if result["success"] else f"Failed (exit {result['returncode']})"
    lines = [f"{icon} *{tool_name}* — {status}"]

    if result["stdout"]:
        lines.append(f"```{result['stdout']}```")
        if result["truncated"]:
            lines.append("_(output truncated — full results saved in the tool's folder)_")

    if not result["success"] and result["stderr"]:
        lines.append(f"*Error:* `{result['stderr'][:500]}`")

    return "\n".join(lines)
