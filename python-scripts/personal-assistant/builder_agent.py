"""
builder_agent.py
Autonomous code-writing agent. Receives a plain-English task + target directory,
calls Claude Sonnet with file-write tools, and writes files to disk.

Public API:
  build_project(task, target_dir) -> Slack-formatted summary string
"""

import logging
import os

import anthropic

from config import ANTHROPIC_API_KEY, PA_SCRIPTS_BASE, REPO_ROOT

log = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_MAX_ITERATIONS = 10  # safety cap — prevents runaway tool-call loops

_SYSTEM_PROMPT = """\
You are an autonomous code builder for Gray Davis (Graydient Media, NYC).
Your job: receive a build task + target directory, then write all the files needed to complete it.

Rules:
- Write complete, working code — no placeholders, no "TODO: fill in"
- Keep it simple — plain HTML/CSS/JS for frontend, Python for backend
- Use create_directory before write_file if the directory doesn't exist yet
- After writing all files, stop — do NOT write a text explanation, just stop calling tools
- File paths passed to write_file must be absolute paths

Tech defaults unless told otherwise:
- Frontend: plain HTML + CSS + vanilla JS (no React, no Node)
- Backend: Python + FastAPI
- Styling: minimal dark theme (#0d0d0d background, #ffffff text, #6C63FF accent)
- Auth: JWT tokens stored in localStorage
"""

BUILDER_TOOLS = [
    {
        "name": "write_file",
        "description": (
            "Write content to a file on disk. Creates the file if it doesn't exist, "
            "overwrites if it does. Always use absolute file paths."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute file path to write",
                },
                "content": {
                    "type": "string",
                    "description": "Full file content to write",
                },
                "description": {
                    "type": "string",
                    "description": "One-line description of what this file does (used in the build summary)",
                },
            },
            "required": ["path", "content", "description"],
        },
    },
    {
        "name": "create_directory",
        "description": "Create a directory (and any missing parent directories).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path of the directory to create",
                },
            },
            "required": ["path"],
        },
    },
]


def _resolve_target_dir(target_dir: str) -> str:
    """
    Turn a relative or absolute target_dir into an absolute path.
    - Absolute paths (start with / or drive letter) are used as-is.
    - Relative paths are joined against REPO_ROOT.
    """
    if os.path.isabs(target_dir):
        return os.path.normpath(target_dir)
    return os.path.normpath(os.path.join(REPO_ROOT, target_dir))


def _scan_existing_files(abs_dir: str, limit: int = 20) -> str:
    """Return a short listing of existing files in the target dir, or 'empty'."""
    if not os.path.isdir(abs_dir):
        return "Directory does not exist yet."
    files = []
    for root, dirs, filenames in os.walk(abs_dir):
        # Skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), abs_dir)
            files.append(rel)
            if len(files) >= limit:
                break
        if len(files) >= limit:
            break
    if not files:
        return "Directory exists but is empty."
    return "Existing files:\n" + "\n".join(f"  {f}" for f in files)


def _do_write_file(path: str, content: str) -> str:
    """Write a file to disk. Returns 'ok' or an error string."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return "ok"
    except Exception as e:
        return f"ERROR: {e}"


def _do_create_directory(path: str) -> str:
    """Create a directory. Returns 'ok' or an error string."""
    try:
        os.makedirs(path, exist_ok=True)
        return "ok"
    except Exception as e:
        return f"ERROR: {e}"


def build_project(task: str, target_dir: str) -> str:
    """
    Build files for `task` inside `target_dir`.
    Returns a Slack-formatted summary of what was created.
    """
    # ── Input validation ──────────────────────────────────────────────────────
    if not task:
        return "No task provided. Tell me what to build."
    if not target_dir or target_dir.strip() in ("", "/", "\\"):
        return "No target directory provided. Tell me where to write the files."

    abs_dir = _resolve_target_dir(target_dir.strip())
    log.info(f"Builder starting. task={task!r} abs_dir={abs_dir}")

    existing = _scan_existing_files(abs_dir)

    # ── Build the initial user message ───────────────────────────────────────
    user_message = (
        f"Task: {task}\n\n"
        f"Target directory (absolute): {abs_dir}\n\n"
        f"{existing}"
    )

    messages = [{"role": "user", "content": user_message}]
    files_built: list[tuple[str, str]] = []  # (relative_path, description)
    errors: list[str] = []

    # ── Agentic tool loop ─────────────────────────────────────────────────────
    for iteration in range(_MAX_ITERATIONS):
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            tools=BUILDER_TOOLS,
            messages=messages,
        )

        log.info(f"Builder iteration {iteration + 1}: stop_reason={response.stop_reason}")

        # Track usage
        try:
            import sys as _sys
            _sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
            from usage_logger import track_response
            track_response(response)
        except Exception:
            pass

        # Record assistant response into history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Claude is done calling tools
            break

        # Execute each tool call
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "write_file":
                path = block.input.get("path", "")
                content = block.input.get("content", "")
                desc = block.input.get("description", "")
                result = _do_write_file(path, content)
                if result == "ok":
                    rel = os.path.relpath(path, abs_dir)
                    files_built.append((rel, desc))
                    log.info(f"Wrote: {path}")
                else:
                    errors.append(f"{os.path.basename(path)}: {result}")
                    log.error(f"Write failed: {path} — {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            elif block.name == "create_directory":
                path = block.input.get("path", "")
                result = _do_create_directory(path)
                log.info(f"Created dir: {path} — {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            else:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Unknown tool: {block.name}",
                })

        messages.append({"role": "user", "content": tool_results})

    # ── Build Slack summary ───────────────────────────────────────────────────
    if not files_built and not errors:
        return "Builder ran but no files were written. The task may need more detail."

    lines = []
    if files_built:
        lines.append(f"Built {len(files_built)} file{'s' if len(files_built) != 1 else ''} in `{target_dir}`:")
        for rel, desc in files_built:
            lines.append(f"  • {rel} — {desc}")
    if errors:
        lines.append(f"\n{len(errors)} error{'s' if len(errors) != 1 else ''}:")
        for e in errors:
            lines.append(f"  ✗ {e}")

    lines.append("Done.")
    return "\n".join(lines)
