# Personal Assistant

## What It Does
- Always-on Slack agent — DM the bot from anywhere (even your phone) and it runs Gray's automation tools on demand
- Claude Sonnet commander decides which of 7 internal tools to call based on plain-English requests
- Queues tasks with words like "tonight" or "later" and runs them overnight at 2am
- Sends a morning status summary at 7am with pending tasks + tool reminders
- Includes `build_project` — an autonomous code-writing sub-agent that scaffolds files directly to disk

## Key Files
- `main.py` — entry point. Starts the Slack listener, registers 2am + 7am scheduled jobs, then loops forever running pending jobs every 30 seconds
- `config.py` — loads `.env`, validates required vars, exposes `PA_QUEUE_HOUR`, `PA_SUMMARY_HOUR`, `PA_SCRIPTS_BASE`, `REPO_ROOT`
- `slack_bot.py` — Slack Socket Mode listener + `send_message()` helper for DMing Gray
- `commander.py` — Claude Sonnet brain with tool_use schema + per-channel conversation history (up to 20 turns)
- `dispatcher.py` — agentic loop. Takes a Slack message, runs the commander, executes any tool_use blocks, feeds results back until Claude stops
- `tool_registry.py` — single source of truth for the 10 automation tools the assistant can launch as subprocesses
- `runner.py` — shells out to the actual tool scripts and formats stdout/stderr for Slack
- `tester_agent.py` — runs a tool, then asks Claude to QA the output (PASS / FAIL + plain-English explanation)
- `builder_agent.py` — the `build_project` autonomous coder. Calls Claude with file-write tools and writes complete code to disk
- `task_queue.py` — add/list/pop/clear overnight tasks (state in `task_queue.json`)
- `scheduler.py` — `schedule` library wiring for the 2am queue run + 7am morning summary
- `install_windows_task.ps1` / `run_agent.bat` — Windows Task Scheduler setup so the agent auto-starts on boot
- `task_queue.json` — runtime state (gitignored). Pending overnight tasks
- `pending_drafts.json` — runtime state (gitignored). Any draft replies awaiting approval
- `agent.log` / `agent-error.log` — runtime logs (gitignored)

## Stack
Python 3 + Claude Sonnet 4.6 (via `anthropic`) + Slack Socket Mode (via `slack-sdk`) + `schedule` + `python-dotenv`

## Run
```bash
cd python-scripts/personal-assistant && python main.py
```

The agent runs forever — DM the Slack bot to use it. Type `help` in the DM to see every tool.

## Env Vars (.env)
Required:
- `ANTHROPIC_API_KEY` — powers commander, tester, and builder agents
- `SLACK_BOT_TOKEN` — `xoxb-...` bot token for DMs
- `SLACK_APP_TOKEN` — `xapp-...` app-level token for Socket Mode
- `SLACK_USER_ID` — Gray's Slack user ID (so the bot knows who to DM)

Optional (have defaults):
- `PA_SCRIPTS_BASE` — path to `python-scripts/` (defaults to parent folder)
- `PA_QUEUE_HOUR` — overnight run hour, 24h format (default `2`)
- `PA_SUMMARY_HOUR` — morning summary hour (default `7`)
- `PA_MAX_OUTPUT_CHARS` — max chars of tool output pasted to Slack (default `2000`)

## Status
LIVE — Commander with 7 tools

## Notes

### The 7 Claude-callable tools (from `commander.py`)
1. `run_tool` — run one of Gray's automation tools right now and return the output
2. `test_tool` — run a tool, then QA the output with Claude → returns PASS or FAIL with reasoning
3. `queue_task` — queue a tool to run overnight at 2am (triggers on "tonight", "later", "overnight")
4. `list_queue` — show what's pending for the overnight run
5. `clear_queue` — cancel all pending overnight tasks
6. `get_status` — report whether the agent is running and what's queued
7. `build_project` — autonomous code-writing sub-agent. Takes a task + target directory and writes complete files to disk

### Automation tools the assistant can launch
Registered in `tool_registry.py`: hook-optimizer, content-researcher, content-pipeline, invoice-system, social-media-analytics, morning-briefing, client-crm, client-onboarding, creator-intel, footage-organizer.

Note: `client-crm` is still listed in the registry but the project has been deleted — remove it next time the registry gets touched. `client-onboarding` is marked `interactive: True` because it uses `input()` and can't run as a subprocess — the assistant will tell Gray to run it manually.

### How the agentic loop works
1. Gray DMs the bot something like "test social-media-analytics"
2. `dispatcher.handle_message()` sends the text to `commander.think()`
3. Claude returns a `tool_use` block (e.g. `test_tool` with `tool_name="social-media-analytics"`)
4. Dispatcher executes the tool, appends the result, calls `think()` again
5. Loop continues up to 5 iterations until Claude returns a plain text reply
6. That reply gets DM'd back to Gray

### Gotchas
- Socket Mode requires both `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` — missing either and startup fails loudly
- Per-channel session history is in-memory only — restarting the agent wipes conversation context
- The `build_project` agent writes files directly to disk with no confirmation — be specific about the target dir
- Commander's system prompt still lists old priorities (Client CRM, Content Researcher V2) — update when priorities shift
