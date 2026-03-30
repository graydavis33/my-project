# Plan: Commander Builder Agent (`build_project` tool)

**Date:** 2026-03-30
**Status:** Implemented
**Request:** Add a `build_project` tool to the Personal Assistant Commander so Gray can DM it build instructions and it actually writes code to disk autonomously.

---

## What This Does

Adds a `builder_agent.py` module to the Personal Assistant that turns Commander into a code-writing agent. When Gray DMs "build the login page for Analytical in web-apps/analytical/frontend/", Commander calls `build_project`, which spins up a Claude Sonnet agent with file-write tools, reasons through the task, and writes the actual files to disk — returning a Slack summary of everything created.

This is the bridge between "Commander as task runner" and "Commander as autonomous builder."

---

## Current State

Commander today has 6 tools: `run_tool`, `test_tool`, `queue_task`, `list_queue`, `clear_queue`, `get_status`. All of these operate on existing scripts — none can create new files or write code. There is no builder capability anywhere in the Personal Assistant stack.

The agentic loop in `dispatcher.py` already handles multi-step tool calls cleanly — adding a new tool just means registering it in commander.py and handling it in dispatcher.py.

---

## What We're Building

- **New file:** `python-scripts/personal-assistant/builder_agent.py` — the core builder module
- **Modified:** `python-scripts/personal-assistant/commander.py` — add `build_project` to `COMMANDER_TOOLS` and system prompt
- **Modified:** `python-scripts/personal-assistant/dispatcher.py` — add `build_project` handler in `_execute_tool`

Nothing else changes. `runner.py`, `tester_agent.py`, `task_queue.py`, `scheduler.py`, `slack_bot.py`, `config.py`, `tool_registry.py` are untouched.

---

## Step-by-Step Tasks

### Step 1: Build `builder_agent.py`

Create `python-scripts/personal-assistant/builder_agent.py`.

This module has one public function: `build_project(task: str, target_dir: str) -> str`

**How it works:**

1. Resolves `target_dir` against `PA_SCRIPTS_BASE` from config (falls back to absolute path if target_dir starts with `/` or `C:\`).
2. Scans `target_dir` for existing files (up to 20 files) so Claude knows what already exists.
3. Calls Claude Sonnet with:
   - A builder system prompt (see below)
   - Two tool_use tools: `write_file` and `create_directory`
   - The task as the first user message
4. Runs a tool execution loop (same pattern as dispatcher.py, max 10 iterations):
   - If Claude calls `write_file` → write the file to disk (create parent dirs if needed)
   - If Claude calls `create_directory` → create the directory
   - Feed the result back into the conversation and call Claude again
5. Collects every file written into a list.
6. Returns a Slack-formatted summary:
   ```
   Built 3 files in web-apps/analytical/frontend/:
   • index.html — login page with email/password form
   • style.css — minimal dark theme
   • auth.js — form submission + JWT storage
   Done.
   ```

**Builder system prompt:**
```
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
```

**Tool schemas for the builder:**

```python
BUILDER_TOOLS = [
    {
        "name": "write_file",
        "description": "Write content to a file on disk. Creates the file if it doesn't exist, overwrites if it does.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path to write"},
                "content": {"type": "string", "description": "Full file content to write"},
                "description": {"type": "string", "description": "One-line description of what this file does (for the summary)"},
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
                "path": {"type": "string", "description": "Absolute path of the directory to create"},
            },
            "required": ["path"],
        },
    },
]
```

**Safety guardrails in `build_project`:**
- `target_dir` must not be empty string or `/`
- Cap at 10 tool iterations to prevent runaway loops
- Catch all file-write exceptions and include them in the result instead of crashing

---

### Step 2: Add `build_project` to `commander.py`

In `COMMANDER_TOOLS`, add a new entry after `get_status`:

```python
{
    "name": "build_project",
    "description": (
        "Build files and write code to disk autonomously. Use this when Gray asks you to build, "
        "create, scaffold, or generate code for a specific project or page. "
        "Requires a task description and a target directory path."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Plain-English description of what to build (e.g. 'build the login page with email/password form')",
            },
            "target_dir": {
                "type": "string",
                "description": "Path to the directory where files should be written (e.g. 'web-apps/analytical/frontend' or an absolute path)",
            },
        },
        "required": ["task", "target_dir"],
    },
},
```

Also update `_system_prompt()` — add one bullet to the capabilities list:
```
- Build new code files to disk (build_project) — use when Gray says "build", "create", "scaffold", or "generate"
```

And add one rule:
```
- When Gray says "build [something]" and gives a target dir → use build_project. If he doesn't give a target dir, ask for it first.
```

---

### Step 3: Add `build_project` handler to `dispatcher.py`

In `_execute_tool`, add a handler after `get_status`:

```python
if tool_name == "build_project":
    import builder_agent
    return builder_agent.build_project(
        task=inputs.get("task", ""),
        target_dir=inputs.get("target_dir", ""),
    )
```

No other changes to dispatcher.py.

---

### Step 4: Smoke Test via Slack DM

Send these DMs to the Personal Assistant and verify:

1. `"build a simple hello world HTML page in web-apps/test-build/"` — should create the directory and write `index.html`, return a summary listing the file.
2. `"build the login page for Analytical in web-apps/analytical/frontend/ — email/password form, dark theme"` — should write `index.html` + `style.css` + `auth.js` (or similar), verify files exist on disk.
3. `"build something"` — Commander should ask for a target directory before calling build_project (not crash).

After each test, verify files actually exist on disk at the specified paths.

---

## How to Verify It Works

- [ ] `python main.py` starts without errors after changes
- [ ] Slack DM "build a hello world page in web-apps/test-build/" → files appear on disk at that path
- [ ] Slack DM "build the login page" (no dir) → Commander asks for target directory
- [ ] No existing tools broken: "test morning-briefing" still returns PASS/FAIL correctly
- [ ] builder_agent.py handles a bad path gracefully (returns error string, doesn't crash the agent)

---

## Notes

- Session history: builder_agent uses its own Claude call with no conversation history — it's a pure function like tester_agent.py. That's the right design.
- File size cap: Claude's output is capped at max_tokens. For large files, increase to 4096 tokens in builder_agent.py if needed.
- Windows paths: `target_dir` like `web-apps/analytical/frontend` should be joined against the repo root. Use `os.path.join(REPO_ROOT, target_dir)` — add `REPO_ROOT` to config.py if it's not there.
- This does not give Commander access to the full filesystem — only paths under the repo root. Don't change that.
- V2 idea: add a `read_file` tool to the builder so Claude can inspect existing files before writing — useful for modifying existing pages rather than creating from scratch.

---

## Implementation Notes

**Implemented:** 2026-03-30

### What Was Built
- `python-scripts/personal-assistant/builder_agent.py` — new module. `build_project(task, target_dir)` spins up Claude Sonnet with `write_file` + `create_directory` tools, runs up to 10 iterations, writes files to disk, returns Slack-formatted summary.
- `python-scripts/personal-assistant/config.py` — added `REPO_ROOT` (resolves to `C:\Users\Gray Davis\my-project`), used by builder_agent to turn relative target paths into absolute paths.
- `python-scripts/personal-assistant/commander.py` — added `build_project` to `COMMANDER_TOOLS` (now 7 tools total) and updated `_system_prompt()` with the new capability + routing rule.
- `python-scripts/personal-assistant/dispatcher.py` — added `build_project` handler in `_execute_tool`.

### Deviations from Plan
- None.

### Issues Encountered
- None. All syntax checks and import dry-runs passed cleanly. `REPO_ROOT` resolves correctly to repo root.
