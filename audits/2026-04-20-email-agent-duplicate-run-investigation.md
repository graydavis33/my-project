# Email Agent — Duplicate-Run Investigation

**Date:** 2026-04-20
**Triggered by:** workspace audit flagged suspected duplicate runs on Mac + VPS
**Scope:** `python-scripts/email-agent/` + deployment configs
**Method:** read-only source inspection (no VPS ssh)

---

## TL;DR

The email agent is **designed to run as a long-lived daemon**, not a once-per-hour cron job. The internal `schedule` library handles the hourly cadence and the 7am–8pm active-hours check itself. This means the **VPS systemd setup is correct** (`Restart=always` keeps the daemon alive). The risk vector is **Mac launchd + VPS simultaneously processing the same Gmail inbox**, not the VPS running twice by itself.

**Most likely actual bug:** if Mac launchd is configured with `StartCalendarInterval` (spawn hourly) instead of `KeepAlive` (daemon mode), every hour launchd creates a brand-new Python process and the previous one never exits — processes stack up until OS reboot.

**Recommended action:** designate the VPS as the sole canonical runner. Disable Mac launchd + Windows Task Scheduler for email-agent. One email-agent process = zero duplicate-run surface area.

---

## What the script actually does

`main.py` entry point (lines 197–244):

1. Builds / refreshes voice profile (30-day TTL)
2. Starts Slack listener in a background thread (`start_listener()`)
3. Restores any pending drafts from disk (`restore_pending_drafts`)
4. Runs email check once immediately if within active hours
5. **Schedules `scheduled_check` to run every 60 minutes via the `schedule` library** (line 236)
6. Enters infinite `while True` loop calling `schedule.run_pending()` every 30s (lines 239–244)

Active-hours gate (lines 157–160, 163–167):
```python
def is_within_active_hours():
    hour = datetime.now().hour
    return START_HOUR <= hour < END_HOUR

def scheduled_check():
    if is_within_active_hours():
        run_email_check()
    else:
        log.info("Outside active hours. Skipping.")
```

**Implication:** the script is meant to run continuously. Launching it via a cron-like "fire every hour" scheduler would create stacking processes, not repeated one-shot runs.

## What VPS deployment actually does

Two sources of truth — and they don't match:

### 1. Committed `deploy/email-agent.service`
```ini
Type=simple
User=root
WorkingDirectory=/root/my-project/python-scripts/email-agent
ExecStart=/root/my-project/python-scripts/email-agent/venv/bin/python main.py
Restart=always
RestartSec=15
StandardOutput=append:/root/my-project/python-scripts/email-agent/agent.log
StandardError=append:/root/my-project/python-scripts/email-agent/agent-error.log
```

### 2. `deploy/vps-setup.sh` (lines 207–226) writes a DIFFERENT service inline
```ini
Type=simple
User=root
WorkingDirectory=${REPO_DIR}/python-scripts/email-agent
ExecStart=${REPO_DIR}/python-scripts/email-agent/venv/bin/python main.py
Restart=on-failure
RestartSec=30
StandardOutput=append:/var/log/email-agent.log
StandardError=append:/var/log/email-agent.log
```

**Drift between the two:**
| Field | committed file | vps-setup.sh inline |
|---|---|---|
| Restart | always | on-failure |
| RestartSec | 15 | 30 |
| Log path | project dir | `/var/log/` |

**Consequence:** whichever source was used to `systemctl enable` wins. Since `vps-setup.sh` explicitly does `systemctl enable email-agent`, the inline version is almost certainly live. The committed `.service` file is ignored unless copied manually.

**This is not a duplicate-run bug — it's a config-drift bug.** Both configs produce a single daemon. But you can't trust what's actually running without `ssh root@72.61.10.152 "systemctl cat email-agent"`.

## What Mac (and Windows) might be doing

### Mac — unknown but risky
- `workflows/email-agent.md` says: "runs hourly 7am–8pm via macOS launchd"
- The script's internal scheduler already handles "hourly 7am–8pm"
- If launchd is configured with `StartCalendarInterval` (fire at specific times), it will:
  1. Launch `python main.py` at, say, 7:00am
  2. That process enters its infinite loop and never exits
  3. At 8:00am, launchd launches a NEW `python main.py` process
  4. Now there are two daemons processing the same Gmail account
  5. By end of day: 13 stacked processes
- If launchd is configured with `KeepAlive` (daemon mode), it would be correct — process runs once, restarts if it crashes

**Can't confirm which without reading the plist file** (likely at `~/Library/LaunchAgents/com.graydient.email-agent.plist` or similar). The Mac isn't connected to this session.

### Windows — similar risk
- README mentions `run_agent.bat` + `install_windows_task.ps1`
- Task Scheduler triggers that fire hourly would have the same stacking problem
- Unknown if currently enabled — Gray can check Task Scheduler UI

## Real duplicate-run symptom vectors

Even if the script itself is race-safe (Gmail label `agent-processed` prevents double-classification), stacking processes cause:

1. **Multiple Slack listeners** — each process starts `start_listener()`. Slack messages get delivered to one socket; button clicks may be handled by whichever listener grabs them first, causing "send" to race.
2. **Duplicate voice profile rebuilds** — two processes both hit the 30-day TTL at the same time, both call `build_voice_profile()` which fetches + analyzes 24 emails. Wasted Claude tokens.
3. **Duplicate invoice payment scans** — `_run_payment_scan()` at line 145 runs after every email check. Two processes = two simultaneous `invoice-system scan-payments` subprocess calls racing on the same Google Sheet.
4. **Race on the `agent-processed` label** — low practical risk because Gmail's label-apply is atomic, but two processes fetching the same batch before either labels it could each draft a reply.
5. **Duplicate followup alerts** — `followup_tracker.check_followups` runs each cycle; two processes = two "follow-up needed" Slack messages for the same thread.

**The most visible symptom would be double Slack draft notifications.** If Gray sees one email generating two Slack DMs with Send/Edit/Skip buttons, that's this bug.

## Why `usage-stats.json` shows zero runs

The workspace audit noted that `usage-stats.json` lists `email-agent` as never-logged. Source check (main.py lines 86–92):

```python
try:
    _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', 'shared'))
    from usage_logger import log_run
    log_run("email-agent")
except Exception:
    pass
```

- Logging is **per-machine** — writes to `~/.my-project-usage.json` on whichever machine is running
- VPS has its own home dir (`/root/.my-project-usage.json`) — NOT synced to git
- `sync_usage.py` only reads the local home file, so VPS runs never make it into the committed `usage-stats.json`
- This is not evidence of failure. It's evidence that the logger is local-only.

**Not a bug in email-agent.** A limitation of the usage-logging design.

## Recommendations (in priority order)

### Immediate — requires 15 min on Mac
1. **Check `~/Library/LaunchAgents/` and `/Library/LaunchDaemons/` for an email-agent plist.**
   - If present, read it. If it has `StartCalendarInterval` or `StartInterval`, you have the stacking bug.
   - Quick kill: `launchctl unload ~/Library/LaunchAgents/com.<name>.email-agent.plist`
2. **Check Windows Task Scheduler for an email-agent task.** Same logic — disable if present.
3. **Pick one canonical runner.** Recommended: VPS. It's always-on and handles its own scheduling.

### Short-term — 30 min
4. **Delete `deploy/email-agent.service`** OR make `vps-setup.sh` use the committed file instead of inlining a conflicting one. Single source of truth for VPS systemd config.
5. **Update `workflows/email-agent.md`** to state: "Runs as a systemd daemon on VPS. Script handles its own 7am–8pm hourly cadence internally — do NOT schedule it externally via cron, launchd, or Task Scheduler."
6. **Verify VPS reality:** `ssh root@72.61.10.152 "systemctl status email-agent && tail -50 /var/log/email-agent.log"` — confirm it's running and logging.

### Long-term — when Gray has appetite
7. **Unify logging.** Make `usage_logger` write to a repo-tracked file instead of `~/`, OR have VPS push its log to a shared endpoint. Currently the dashboard can never reflect VPS runs.
8. **Kill-switch pattern.** Add a single file `python-scripts/email-agent/.canonical-runner` containing the hostname where the agent is supposed to run. Script refuses to start if `socket.gethostname()` doesn't match. Belt-and-suspenders protection against accidentally re-enabling Mac launchd.

---

**Confidence:** HIGH on architecture analysis (code is self-evident). MEDIUM on actual Mac state (can't read the plist from this session). The recommendations above are safe regardless — they assume the worst case and fix it.
