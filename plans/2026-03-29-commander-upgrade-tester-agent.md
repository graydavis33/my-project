# Plan: Commander Upgrade + Tester Agent

**Date:** 2026-03-29
**Status:** Draft
**Request:** Upgrade the Personal Assistant Commander (swap Haiku intent-parser for Claude Sonnet with conversation history) and add a Tester Agent (runs a tool, analyzes output, returns PASS/FAIL verdict).

---

## What This Does

Transforms the Personal Assistant from a dumb command router into a true reasoning agent. Instead of Haiku parsing a fixed intent schema, Claude Sonnet maintains full conversation history per session — so it remembers context, reasons across messages, and uses tool_use to decide what actions to take. The Tester Agent wraps any tool run with Claude analysis: it reads stdout/stderr and tells you in plain English whether the tool worked and why.

## Current State

**brain.py** — Claude Haiku, intent-only. Returns a JSON schema with 7 fixed intents. No memory, no reasoning beyond "which intent is this?" Resets after every single message.

**dispatcher.py** — reads the intent JSON and routes to runner, task_queue, or tool_registry. Works fine but is only as smart as brain.py.

**runner.py** — runs tools as subprocesses, returns raw `{success, stdout, stderr, returncode}`. Does zero analysis of the output. Stays as-is.

**slack_bot.py / scheduler.py / task_queue.py / config.py** — all solid. Not touched.

**Missing:** no tester agent, no conversation memory, no agentic tool_use loop.

## What We're Building

- **New:** `commander.py` — replaces brain.py entirely. Claude Sonnet agent with:
  - In-memory conversation history per Slack channel (resets on process restart, perfect for now)
  - Anthropic tool_use — Claude decides which tools to call, not a fixed intent schema
  - System prompt that establishes Gray's executive assistant persona + full awareness of all tools
  - Max 20 turns of history per session (older messages pruned to keep token cost low)
- **New:** `tester_agent.py` — QA analysis module:
  - Calls runner.run_tool() to execute the tool
  - Feeds stdout/stderr/exit code to Claude Sonnet with a QA analyst prompt
  - Returns Slack-formatted PASS/FAIL verdict with error explanation if failed
- **Modified:** `dispatcher.py` — rewritten as an agentic loop:
  - Adds message to session history
  - Calls commander.think() → Claude returns tool_use blocks and/or text
  - Executes each tool call, feeds results back into the conversation
  - Loops until Claude returns a final text reply with no more tool calls
- **Deleted:** `brain.py` — fully replaced by commander.py

## Step-by-Step Tasks

### Step 1: Build commander.py

Create `python-scripts/personal-assistant/commander.py`.

This module owns:
1. `_sessions` — a dict mapping Slack channel ID → list of Anthropic message dicts (conversation history)
2. `COMMANDER_TOOLS` — Anthropic tool_use schema for 6 tools: `run_tool`, `test_tool`, `queue_task`, `list_queue`, `clear_queue`, `get_status`
3. `think(channel_id, user_text)` — adds user message to history, calls Claude Sonnet with tools, returns the full response object (may contain tool_use blocks)
4. `add_tool_result(channel_id, tool_use_id, tool_name, result_text)` — adds a tool_result turn to history
5. `add_assistant_reply(channel_id, content)` — adds Claude's reply to history so it remembers what it said
6. `prune_history(channel_id)` — keeps last 20 turns max

System prompt for Claude:
```
You are Gray's executive assistant — smart, direct, and efficient.
Gray is a freelance videographer and AI operator building automation tools.
You have access to his full automation toolkit. You can run tools, queue overnight tasks,
check status, and test tools to validate they're working.

When Gray asks a general question, answer it. When he wants a tool run, use run_tool.
When he wants something tested/validated, use test_tool.
When he says "tonight" or "later", use queue_task.
Keep replies concise — Gray reads these on his phone.

Available tools: [auto-populated from TOOLS registry]
```

### Step 2: Build tester_agent.py

Create `python-scripts/personal-assistant/tester_agent.py`.

The module has one public function: `test_tool(tool_name: str, args: list) -> str`

What it does:
1. Calls `runner.run_tool(tool_name, args)` to get `{success, stdout, stderr, returncode, truncated}`
2. Builds a prompt: "Here is the output from running [tool_name] with args [args]. Analyze it."
3. Calls Claude Sonnet with a QA analyst system prompt:
   - State PASS or FAIL
   - 2-3 sentence summary of what the tool did
   - If FAIL: what the specific error is, likely cause, and what to fix
   - If PASS: note any warnings or unusual output worth flagging
   - Keep it under 300 words — this goes to Slack
4. Returns the formatted Slack reply string

This module is dumb by design — it doesn't need conversation history. It's a pure function: input = raw output, return = human analysis.

### Step 3: Rewrite dispatcher.py

New `dispatcher.py` — agentic loop replacing the old intent-routing logic.

`handle_message(text: str, channel: str) -> str`:

```
1. commander.think(channel, text)  →  response
2. while response has tool_use blocks:
     for each tool_use block:
       - execute the tool (run_tool, test_tool, queue_task, etc.)
       - call commander.add_tool_result(channel, tool_use_id, result)
     commander.think(channel, "")  →  next response  (empty text = tool result continuation)
3. extract final text reply from response
4. commander.add_assistant_reply(channel, reply)
5. return reply
```

Tool execution mapping inside dispatcher:
- `run_tool` → `runner.run_tool()` + `runner.format_result()`
- `test_tool` → `tester_agent.test_tool()`
- `queue_task` → `task_queue.add_task()` + confirmation message
- `list_queue` → `task_queue.format_queue_list()`
- `clear_queue` → `task_queue.clear_queue()`
- `get_status` → build status string (same as current status handler)

### Step 4: Delete brain.py

Remove `brain.py` — it is fully replaced by `commander.py`.

Also update the import in `dispatcher.py` — remove `from brain import parse_intent`.

### Step 5: Smoke Test

Before considering this done, verify these 4 scenarios work end-to-end via Slack DM:

1. `"what should I work on today?"` — Claude reasons from its system prompt context, gives a useful answer (not just "I don't understand")
2. `"test morning-briefing"` — runs the tool, returns PASS/FAIL with explanation
3. `"run social media analytics and tell me one insight from the output"` — runs tool, reads output, gives an insight (multi-step: tool_use → result → reasoning)
4. Send 3 messages in a row — the 3rd response references something from message 1 (proves history works)

## How to Verify It Works

- [ ] `python main.py` starts without errors
- [ ] Slack DM "status" returns agent status (regression test — this worked before)
- [ ] Slack DM "what should I focus on today?" returns a reasoned answer
- [ ] Slack DM "test hook-optimizer" runs the tool and returns PASS/FAIL analysis
- [ ] Slack DM "run creator-intel tonight" queues the task (not runs immediately)
- [ ] Two-message context test: send "I'm thinking about testing my tools" then "which one should I start with?" — second reply should reference the first message

## Notes

- Session history is in-memory only — resets when the process restarts. That's intentional for now. Persistent memory (SQLite or JSON) is a V2 upgrade.
- The `handle_message` signature in dispatcher.py needs to accept `channel` as a second arg. Update the call in `slack_bot.py` line ~71 to pass `channel=channel`.
- Max tool_use loop iterations: cap at 5 to prevent infinite loops if Claude keeps calling tools. After 5, return whatever text Claude has so far.
- Keep runner.py, task_queue.py, scheduler.py, config.py, and slack_bot.py untouched.
- Use `claude-sonnet-4-6` for both commander and tester agent. Haiku was only used because it was a dumb parser — Sonnet is worth the cost here.
