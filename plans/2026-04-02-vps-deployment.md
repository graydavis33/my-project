# Plan: VPS Deployment — Email Agent, Morning Briefing, Invoice Scan

**Date:** 2026-04-02
**Status:** Draft
**Request:** Deploy Email Agent, Morning Briefing, and Invoice System to Hostinger VPS so they run 24/7 in the cloud instead of requiring a local terminal.

---

## What This Does

Moves three automation tools off Gray's local machine and onto the Hostinger VPS (Ubuntu 24.04, `72.61.10.152`) as always-on systemd services. Email Agent checks Gmail hourly and sends Slack drafts. Morning Briefing fires at 8am daily. Invoice scan-all runs daily at 9am. No machine needs to be on for any of this.

## Current State

- **Email Agent** — LIVE on Mac (runs via launchd). Long-running process with hourly Gmail check + Slack Socket Mode listener.
- **Morning Briefing** — Built on Windows. Has `--schedule` flag, fires at 8am. Needs .env setup.
- **Invoice System** — LIVE on Mac (CLI). Automated scan-payments already called by email-agent hourly. scan-receipts not yet scheduled anywhere.
- **VPS** — Ubuntu 24.04, Python 3.12 pre-installed, `ssh root@72.61.10.152`. n8n already running via Docker — we stay completely separate from it.

## What We're Building

- `deploy/email-agent.service` — systemd service file for Email Agent
- `deploy/morning-briefing.service` — systemd service file for Morning Briefing
- `deploy/invoice-scan.service` — systemd service file for Invoice scan-all (daily)
- `deploy/setup-vps.sh` — one-shot bash script that runs on the VPS to clone the repo, create virtualenvs, install deps, and install all three services
- `.env` files created manually on the VPS (never in the repo) for each project
- `credentials.json` + `token.json` files uploaded to the VPS via SCP (gitignored, manual step)

## Step-by-Step Tasks

### Step 1: Create systemd service files

Create `deploy/email-agent.service`:
```ini
[Unit]
Description=Graydient Media Email Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/my-project/python-scripts/email-agent
ExecStart=/root/my-project/python-scripts/email-agent/venv/bin/python main.py
Restart=always
RestartSec=15
StandardOutput=append:/root/my-project/python-scripts/email-agent/agent.log
StandardError=append:/root/my-project/python-scripts/email-agent/agent-error.log

[Install]
WantedBy=multi-user.target
```

Create `deploy/morning-briefing.service`:
```ini
[Unit]
Description=Graydient Media Morning Briefing
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/my-project/python-scripts/morning-briefing
ExecStart=/root/my-project/python-scripts/morning-briefing/venv/bin/python main.py --schedule
Restart=always
RestartSec=15
StandardOutput=append:/root/my-project/python-scripts/morning-briefing/briefing.log
StandardError=append:/root/my-project/python-scripts/morning-briefing/briefing.log

[Install]
WantedBy=multi-user.target
```

Create `deploy/invoice-scan.service`:
```ini
[Unit]
Description=Graydient Media Invoice Scanner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/my-project/python-scripts/invoice-system
ExecStart=/root/my-project/python-scripts/invoice-system/venv/bin/python main.py scan-all --schedule --time 09:00
Restart=always
RestartSec=15
StandardOutput=append:/root/my-project/python-scripts/invoice-system/invoice_scan.log
StandardError=append:/root/my-project/python-scripts/invoice-system/invoice_scan.log

[Install]
WantedBy=multi-user.target
```

### Step 2: Create the VPS setup script

Create `deploy/setup-vps.sh` — runs on the VPS after SSH in. It:
1. Installs `python3-venv` and `python3-pip` if needed
2. Clones the GitHub repo to `/root/my-project`
3. Creates a Python virtualenv inside each project folder (`venv/`)
4. Installs each project's `requirements.txt` into its venv
5. Copies the three `.service` files to `/etc/systemd/system/`
6. Reloads systemd, enables and starts each service

### Step 3: Manual pre-deploy steps (Gray does these)

Before running the setup script, Gray must:

1. **Upload credentials for Email Agent** (from Mac/Windows terminal):
   ```bash
   scp python-scripts/email-agent/credentials.json root@72.61.10.152:/tmp/ea-credentials.json
   scp python-scripts/email-agent/token.json root@72.61.10.152:/tmp/ea-token.json
   ```

2. **Upload credentials for Invoice System**:
   ```bash
   scp python-scripts/invoice-system/credentials.json root@72.61.10.152:/tmp/inv-credentials.json
   scp python-scripts/invoice-system/token.json root@72.61.10.152:/tmp/inv-token.json
   ```

3. **Upload credentials for Morning Briefing** (if it has its own Google token):
   ```bash
   scp python-scripts/morning-briefing/token.json root@72.61.10.152:/tmp/mb-token.json
   ```

These land in `/tmp/` first, then the setup script moves them to the right project folders.

### Step 4: Create .env files on the VPS

After SSH in, Gray creates `.env` files for each project. The setup script creates blank templates — Gray fills in the values. Keys needed:

**email-agent/.env:**
```
ANTHROPIC_API_KEY=
SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
SLACK_USER_ID=
GMAIL_CREDENTIALS_PATH=credentials.json
```

**morning-briefing/.env:**
```
ANTHROPIC_API_KEY=
SLACK_BOT_TOKEN=
SLACK_USER_ID=
INVOICE_SHEET_ID=1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw
ANALYTICS_SHEET_ID=19xls01LAgXzhwR970geSjABFtWTd1GhQ6-goBLv6FMI
EMAIL_AGENT_DIR=/root/my-project/python-scripts/email-agent
GOOGLE_CREDENTIALS_PATH=/root/my-project/python-scripts/morning-briefing/credentials.json
```

**invoice-system/.env:**
```
ANTHROPIC_API_KEY=
GOOGLE_SHEET_ID=1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw
GMAIL_CREDENTIALS_PATH=credentials.json
```

### Step 5: Run the setup script on the VPS

```bash
ssh root@72.61.10.152
bash /root/my-project/deploy/setup-vps.sh
```

### Step 6: Verify services are running

```bash
systemctl status email-agent
systemctl status morning-briefing
systemctl status invoice-scan
journalctl -u email-agent -n 50
```

---

## How to Verify It Works

- [ ] `systemctl status email-agent` shows `Active: running`
- [ ] `systemctl status morning-briefing` shows `Active: running`
- [ ] `systemctl status invoice-scan` shows `Active: running`
- [ ] Tail `agent.log` on the VPS — see hourly check logs appearing
- [ ] Wait for or manually trigger the morning briefing — Slack DM arrives
- [ ] Check that email-agent's log shows no auth errors (Gmail OAuth working)
- [ ] On Mac: stop the launchd email-agent so it's only running on the VPS (one place)

---

## Notes

- **n8n stays untouched** — it runs in Docker on this same VPS. Our scripts are plain Python processes, no conflict.
- **Invoice interactive commands** (`create-invoice`, `add-expense`) still require SSH + terminal. No change there — they're one-off manual actions.
- **Email Agent calls scan-payments hourly** already (hardcoded in `main.py`). The `invoice-scan` service handles `scan-receipts` + `scan-payments` at 9am as a full daily sweep. Small overlap is fine — the payment scanner deduplicates.
- **Token expiry risk:** Gmail OAuth tokens expire. If the token was generated on Mac, it may need to be re-generated. If the agent crashes with auth errors after ~7 days, we'll need a re-auth flow. Ubuntu 24.04 has no browser so re-auth must be done with a local tunnel or by re-generating the token on Mac and SCP-ing it up. Flag this if it happens.
- **Morning Briefing credentials:** It uses Google Sheets (gspread) which may share the same credentials.json as invoice-system. Check if it has its own token.json before uploading — may be able to reuse.
