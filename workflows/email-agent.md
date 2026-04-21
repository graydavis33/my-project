# Workflow: Email Agent

**Status:** LIVE — systemd daemon on VPS (`72.61.10.152`). 7am–8pm hourly cadence is handled internally by the script; no external scheduler required.
**Cost:** Minimal — Claude Sonnet per email classified + drafted
**Script:** `python-scripts/email-agent/`

---

## Objective

Long-lived daemon. Watches Gmail, classifies incoming emails, drafts replies in Gray's voice, sends them to Slack for one-click approval, chases follow-ups, and triggers the invoice payment scanner on every cycle.

---

## Architecture (read before changing anything)

`main.py` is a **daemon, not a one-shot script.** It:

1. Builds the voice profile if missing; refreshes if >30 days old
2. Starts the Slack listener in a background thread
3. Restores any pending drafts from disk (`draft_stats.json`)
4. Runs an immediate email check if within active hours
5. Schedules `scheduled_check()` to run every 60 minutes via the `schedule` library
6. Sits in `while True` polling for scheduled work every 30s

**DO NOT** wire this up to cron, launchd `StartCalendarInterval`, or Windows Task Scheduler "fire every hour". Each spawn would create a new daemon and they'd stack up forever. Run it as a single always-on process. On VPS that means systemd `Restart=always`. On local dev, launch it once in a terminal.

See `audits/2026-04-20-email-agent-duplicate-run-investigation.md` for the full analysis.

---

## How to Run (Manual / Dev)

```bash
cd python-scripts/email-agent
python main.py
# Ctrl+C to stop
```

---

## What Each Hourly Cycle Does

1. Fetches new Gmail messages not yet labeled `agent-processed`
2. Claude classifies each: `needs_reply`, `fyi_only`, or `ignore`
3. Marks each as `agent-processed` immediately — prevents double-handling on restart
4. For `needs_reply`: applies `Agent/Needs Reply` label, Claude drafts a reply using the voice profile, sends draft to Slack DM with **Send / Edit / Skip** buttons
5. For everything else: archives the email (no action needed)
6. **Fires `invoice-system scan-payments --days 2`** as a subprocess — income payments are logged automatically without a second scheduler
7. **Follow-up tracker** — scans sent replies awaiting a response >3 days, sends a consolidated Slack alert for any that are overdue

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
| Duplicate messages in Slack | You have two daemons running. See investigation report. Run `systemctl status email-agent` on VPS; check for a Mac launchd or Windows Task Scheduler job fighting it. Kill the non-canonical one. |
| Agent not running on VPS | `ssh root@72.61.10.152 "systemctl status email-agent"` and `tail -50 /var/log/email-agent.log` |
| Config drift (committed .service vs vps-setup.sh) | `vps-setup.sh` writes its own inline service; committed `deploy/email-agent.service` may not match what's actually running |

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

- Only checks 7am–8pm — emails outside those hours get processed on the next cycle inside window
- Voice profile quality improves over time as more sent emails are analyzed
- Invoice payment scan integration means every email-agent cycle also touches `python-scripts/invoice-system/`. Timeout is 120s; failure is logged, not fatal
- Windows helper scripts (`run_agent.bat`, `install_windows_task.ps1`) exist but the **VPS is canonical.** Don't enable Windows scheduling unless you've first disabled the VPS daemon.
