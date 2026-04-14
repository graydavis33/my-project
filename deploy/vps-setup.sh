#!/usr/bin/env bash
# vps-setup.sh
# Run this once from your local machine to deploy Email Agent, Morning Briefing,
# and Invoice System to the Hostinger VPS.
#
# Usage: bash vps-setup.sh
#
# What it does:
#   1. Tests SSH connection to VPS
#   2. Collects .env values (auto-reads from local .env files where possible)
#   3. Copies Google OAuth files (credentials.json + token.json) to VPS
#   4. SSHs into VPS and:
#      - Installs Python3, pip, git
#      - Clones/updates the GitHub repo
#      - Creates per-tool venvs and installs requirements
#      - Writes .env files for each tool
#      - Creates systemd service for Email Agent (always-on)
#      - Creates cron jobs for Morning Briefing (8am daily) and Invoice System (9am daily)
#      - Prints final status

set -euo pipefail

# ─── Constants ────────────────────────────────────────────────────────────────
VPS_USER="root"
VPS_IP="72.61.10.152"
REPO_URL="https://github.com/graydavis33/my-project"
REPO_DIR="/root/my-project"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║         Graydient Media — VPS Setup              ║"
echo "║   Email Agent · Morning Briefing · Invoice       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Target: ${VPS_USER}@${VPS_IP}"
echo ""

# ─── Section 1: SSH Preflight ─────────────────────────────────────────────────
echo "=== [1/4] Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "${VPS_USER}@${VPS_IP}" "echo 'SSH OK'" 2>/dev/null; then
    echo ""
    echo "ERROR: Cannot connect to VPS via SSH."
    echo ""
    echo "To fix this, do ONE of the following:"
    echo "  Option A (password): Remove -o BatchMode=yes and re-run — you'll be prompted for password."
    echo "  Option B (SSH key):  Run: ssh-copy-id ${VPS_USER}@${VPS_IP}"
    echo ""
    echo "Get your SSH password from: Hostinger Panel → VPS → Manage → SSH Access"
    exit 1
fi
echo "  SSH connection OK."
echo ""

# ─── Helper: read a value from a local .env file ──────────────────────────────
get_local_env_value() {
    local file="$1"
    local key="$2"
    if [[ -f "$file" ]]; then
        grep -E "^${key}=" "$file" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' || true
    fi
}

# ─── Helper: prompt for a value, offering to use local .env if available ──────
prompt_env_var() {
    local key="$1"
    local local_env_file="$2"
    local is_secret="${3:-true}"

    local local_val
    local_val=$(get_local_env_value "$local_env_file" "$key")

    if [[ -n "$local_val" ]]; then
        local masked="${local_val:0:6}..."
        read -r -p "  ${key} — found in local .env [${masked}]. Use it? (Y/n): " use_local
        if [[ "$use_local" != "n" && "$use_local" != "N" ]]; then
            echo "$local_val"
            return
        fi
    fi

    if [[ "$is_secret" == "true" ]]; then
        read -r -s -p "  ${key}: " val
        echo "" >&2
    else
        read -r -p "  ${key}: " val
    fi
    echo "$val"
}

# ─── Section 2: Collect .env values locally ───────────────────────────────────
echo "=== [2/4] Collecting environment variables..."
echo "    (Values will be written to .env files on the VPS — never committed to git)"
echo ""

EA_ENV="${SCRIPT_DIR}/python-scripts/email-agent/.env"
INV_ENV="${SCRIPT_DIR}/python-scripts/invoice-system/.env"
MB_ENV="${SCRIPT_DIR}/python-scripts/morning-briefing/.env"

echo "--- Shared ---"
ANTHROPIC_API_KEY=$(prompt_env_var "ANTHROPIC_API_KEY" "$EA_ENV")

echo ""
echo "--- Slack ---"
SLACK_BOT_TOKEN=$(prompt_env_var "SLACK_BOT_TOKEN" "$EA_ENV")
SLACK_APP_TOKEN=$(prompt_env_var "SLACK_APP_TOKEN" "$EA_ENV")
SLACK_USER_ID=$(prompt_env_var "SLACK_USER_ID" "$EA_ENV" "false")
SLACK_PAYMENTS_CHANNEL_ID=$(prompt_env_var "SLACK_PAYMENTS_CHANNEL_ID" "$INV_ENV" "false")

echo ""
echo "--- Google Sheets ---"
GOOGLE_SHEET_ID=$(prompt_env_var "GOOGLE_SHEET_ID" "$INV_ENV" "false")
INVOICE_SHEET_ID=$(prompt_env_var "INVOICE_SHEET_ID" "$MB_ENV" "false")
ANALYTICS_SHEET_ID=$(prompt_env_var "ANALYTICS_SHEET_ID" "$MB_ENV" "false")

echo ""
echo "--- Morning Briefing ---"
BRIEFING_CHANNEL_ID=$(prompt_env_var "BRIEFING_CHANNEL_ID" "$MB_ENV" "false")
if [[ -z "$BRIEFING_CHANNEL_ID" ]]; then
    BRIEFING_CHANNEL_ID="$SLACK_USER_ID"
    echo "  BRIEFING_CHANNEL_ID not set — defaulting to SLACK_USER_ID"
fi

echo ""
echo "  All values collected."
echo ""

# ─── Section 3: Remote Setup via SSH ──────────────────────────────────────────
echo "=== [3/4] Running remote setup on VPS..."
echo "    (This will take 2-5 minutes on first run)"
echo ""

ssh "${VPS_USER}@${VPS_IP}" bash <<ENDSSH
set -euo pipefail

REPO_DIR="${REPO_DIR}"
REPO_URL="${REPO_URL}"

echo ""
echo "--- [3a] Installing system packages..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv git > /dev/null
echo "  python3, pip3, git, python3-venv: OK"

echo ""
echo "--- [3b] Cloning / updating repo..."
if [[ -d "\${REPO_DIR}/.git" ]]; then
    echo "  Repo already exists. Pulling latest..."
    git -C "\${REPO_DIR}" pull --quiet
else
    echo "  Cloning repo..."
    git clone --quiet "${REPO_URL}" "\${REPO_DIR}"
fi
echo "  Repo: OK"

echo ""
echo "--- [3c] Setting up per-tool virtual environments..."
for TOOL in email-agent invoice-system morning-briefing; do
    TOOL_DIR="\${REPO_DIR}/python-scripts/\${TOOL}"
    VENV_DIR="\${TOOL_DIR}/venv"

    if [[ ! -d "\${VENV_DIR}" ]]; then
        echo "  [\${TOOL}] Creating venv..."
        python3 -m venv "\${VENV_DIR}"
    else
        echo "  [\${TOOL}] Venv already exists."
    fi

    echo "  [\${TOOL}] Installing requirements..."
    "\${VENV_DIR}/bin/pip" install --upgrade pip --quiet
    "\${VENV_DIR}/bin/pip" install -r "\${TOOL_DIR}/requirements.txt" --quiet
    echo "  [\${TOOL}] OK"
done

echo ""
echo "--- [3d] Writing .env files..."

cat > "\${REPO_DIR}/python-scripts/email-agent/.env" <<EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
SLACK_APP_TOKEN=${SLACK_APP_TOKEN}
SLACK_USER_ID=${SLACK_USER_ID}
EOF
echo "  email-agent/.env: written"

cat > "\${REPO_DIR}/python-scripts/invoice-system/.env" <<EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
GOOGLE_SHEET_ID=${GOOGLE_SHEET_ID}
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
SLACK_PAYMENTS_CHANNEL_ID=${SLACK_PAYMENTS_CHANNEL_ID}
EOF
echo "  invoice-system/.env: written"

cat > "\${REPO_DIR}/python-scripts/morning-briefing/.env" <<EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
SLACK_USER_ID=${SLACK_USER_ID}
BRIEFING_CHANNEL_ID=${BRIEFING_CHANNEL_ID}
INVOICE_SHEET_ID=${INVOICE_SHEET_ID}
ANALYTICS_SHEET_ID=${ANALYTICS_SHEET_ID}
EMAIL_AGENT_DIR=\${REPO_DIR}/python-scripts/email-agent
EOF
echo "  morning-briefing/.env: written"

echo ""
echo "--- [3e] Creating Email Agent systemd service..."
cat > /etc/systemd/system/email-agent.service <<EOF
[Unit]
Description=Gray Davis Email Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=\${REPO_DIR}/python-scripts/email-agent
ExecStart=\${REPO_DIR}/python-scripts/email-agent/venv/bin/python main.py
Restart=on-failure
RestartSec=30
StandardOutput=append:/var/log/email-agent.log
StandardError=append:/var/log/email-agent.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable email-agent --quiet
systemctl restart email-agent
echo "  email-agent.service: enabled and started"

echo ""
echo "--- [3f] Installing cron jobs..."
(
    crontab -l 2>/dev/null \
        | grep -v "morning-briefing/main.py" \
        | grep -v "invoice-system/main.py"
    echo "0 8 * * * cd \${REPO_DIR}/python-scripts/morning-briefing && \${REPO_DIR}/python-scripts/morning-briefing/venv/bin/python main.py >> /var/log/morning-briefing.log 2>&1"
    echo "0 9 * * * cd \${REPO_DIR}/python-scripts/invoice-system && \${REPO_DIR}/python-scripts/invoice-system/venv/bin/python main.py scan-all >> /var/log/invoice-scan.log 2>&1"
) | crontab -
echo "  Morning Briefing: daily at 8:00am"
echo "  Invoice scan-all: daily at 9:00am"

echo ""
echo "--- [3g] Final status ---"
echo ""
systemctl status email-agent --no-pager -l || true
echo ""
echo "Cron entries:"
crontab -l | grep -E "morning-briefing|invoice-system" || echo "  (none found — check above for errors)"

echo ""
echo "════════════════════════════════════════════════════"
echo "  Remote setup complete!"
echo "════════════════════════════════════════════════════"
ENDSSH

# ─── Section 4: Copy OAuth Files from Local to VPS ────────────────────────────
echo ""
echo "=== [4/4] Copying Google OAuth files to VPS..."
echo "    (credentials.json + token.json for each tool)"
echo ""

TOOLS_AND_DIRS=(
    "email-agent:python-scripts/email-agent"
    "invoice-system:python-scripts/invoice-system"
    "morning-briefing:python-scripts/morning-briefing"
)

COPIED=0
MISSING=0

for ENTRY in "${TOOLS_AND_DIRS[@]}"; do
    TOOL="${ENTRY%%:*}"
    LOCAL_DIR="${SCRIPT_DIR}/${ENTRY##*:}"
    REMOTE_DIR="${REPO_DIR}/${ENTRY##*:}"

    for FILE in credentials.json token.json; do
        LOCAL_PATH="${LOCAL_DIR}/${FILE}"
        if [[ -f "$LOCAL_PATH" ]]; then
            echo "  Copying ${TOOL}/${FILE}..."
            scp -q "$LOCAL_PATH" "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/${FILE}"
            COPIED=$((COPIED + 1))
        else
            echo "  WARN: ${TOOL}/${FILE} not found locally — skipping"
            MISSING=$((MISSING + 1))
        fi
    done
done

echo ""
echo "  Copied: ${COPIED} file(s)   Missing/skipped: ${MISSING} file(s)"

if [[ $MISSING -gt 0 ]]; then
    echo ""
    echo "  NOTE: Missing OAuth files mean those tools can't access Gmail/Google Sheets."
    echo "  To copy a file later, run:"
    echo "    scp python-scripts/TOOL/token.json ${VPS_USER}@${VPS_IP}:${REPO_DIR}/python-scripts/TOOL/token.json"
fi

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║               Setup Complete!                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "What's running on your VPS:"
echo "  • Email Agent     — systemd service (hourly, 7am–8pm)"
echo "  • Morning Briefing — cron job (daily 8:00am)"
echo "  • Invoice System   — cron job (daily 9:00am)"
echo ""
echo "Useful commands:"
echo "  Check Email Agent:   ssh ${VPS_USER}@${VPS_IP} \"systemctl status email-agent\""
echo "  View Email Agent log: ssh ${VPS_USER}@${VPS_IP} \"tail -50 /var/log/email-agent.log\""
echo "  Test Morning Briefing manually:"
echo "    ssh ${VPS_USER}@${VPS_IP} \"cd ${REPO_DIR}/python-scripts/morning-briefing && venv/bin/python main.py\""
echo "  Test Invoice scan manually:"
echo "    ssh ${VPS_USER}@${VPS_IP} \"cd ${REPO_DIR}/python-scripts/invoice-system && venv/bin/python main.py scan-all\""
echo ""
echo "⚠️  IMPORTANT — Google OAuth tokens expire every 7 days (testing mode)."
echo "   When a tool fails with '401 Token expired':"
echo "   1. Re-run the tool locally once (browser re-auth)"
echo "   2. Run this to refresh the VPS token:"
echo "      scp python-scripts/TOOL/token.json ${VPS_USER}@${VPS_IP}:${REPO_DIR}/python-scripts/TOOL/token.json"
echo "   3. Restart email agent if needed: ssh ${VPS_USER}@${VPS_IP} 'systemctl restart email-agent'"
echo ""
echo "   Permanent fix: Google Cloud Console → publish OAuth app (Testing → Production)"
echo "   This removes the 7-day limit entirely."
echo ""
