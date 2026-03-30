# Workflow: Email Agent

**Status:** LIVE on Mac — runs hourly 7am–8pm via macOS launchd
**Cost:** Minimal — Claude Sonnet per email classified + drafted
**Script:** `python-scripts/email-agent/`

---

## Objective

Monitor Gmail every hour, classify incoming emails, draft replies in Gray's voice, and send them to Slack for one-click approval. Keeps inbox managed without manual checking.

---

## How to Run (Manual)

```bash
cd python-scripts/email-agent
python main.py
```

Runs once and exits. On Mac it's scheduled via launchd — no manual run needed during the day.

---

## What It Does (Step by Step)

1. Fetches new Gmail messages not yet labeled `agent-processed`
2. Claude classifies each: `needs_reply`, `fyi_only`, or `ignore`
3. For `needs_reply`: Claude drafts a reply using Gray's voice profile
4. Sends to Slack DM with **Send / Edit / Skip** buttons
5. Applies Gmail labels automatically: Agent/Needs Reply, Agent/FYI Only, Agent/Ignore
6. Marks emails `agent-processed` so they're never double-handled

---

## Voice Profile

- Built from 24 sent emails — stored in `voice_profile.txt`
- Auto-refreshes every 30 days from new sent emails
- To manually refresh: delete `voice_profile.txt` and restart — it rebuilds on next run

---

## How to Handle Failures

| Problem | Fix |
|---------|-----|
| Not receiving Slack messages | Check `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_USER_ID` in `.env` |
| Gmail auth error | OAuth token expired — re-run auth flow. Check `GMAIL_CREDENTIALS_PATH` in `.env` |
| Tone feels off | Provide email screenshots to calibrate voice profile further |
| Duplicate messages in Slack | Check if `agent-processed` label is being applied correctly in Gmail |
| Agent not running on Mac | Check launchd: `launchctl list | grep email` |

---

## Env Vars Required

```
ANTHROPIC_API_KEY
SLACK_BOT_TOKEN
SLACK_APP_TOKEN
SLACK_USER_ID
GMAIL_CREDENTIALS_PATH
```

---

## Known Constraints

- Only runs 7am–8pm — emails outside those hours get processed on next morning's run
- Voice profile quality improves over time as more sent emails are analyzed
- Windows setup exists (`run_agent.bat` + `install_windows_task.ps1`) but primary is Mac
