#!/bin/bash
# setup-vps.sh
# Run this once on the Hostinger VPS to deploy Email Agent, Morning Briefing, and Invoice Scanner.
# Usage: bash /root/my-project/deploy/setup-vps.sh

set -e

REPO_URL="https://github.com/graydavis33/my-project.git"
REPO_DIR="/root/my-project"
DEPLOY_DIR="$REPO_DIR/deploy"

echo "============================================"
echo "  Graydient Media — VPS Setup"
echo "============================================"

# ── 1. System dependencies ─────────────────────────────────────────────────
echo ""
echo "[1/6] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip git
echo "  Done."

# ── 2. Clone or update the repo ────────────────────────────────────────────
echo ""
echo "[2/6] Cloning repo..."
if [ -d "$REPO_DIR/.git" ]; then
    echo "  Repo already exists. Pulling latest..."
    git -C "$REPO_DIR" pull
else
    git clone "$REPO_URL" "$REPO_DIR"
    echo "  Cloned to $REPO_DIR"
fi

# ── 3. Create virtualenvs and install requirements ─────────────────────────
echo ""
echo "[3/6] Setting up Python virtualenvs..."

for PROJECT in email-agent morning-briefing invoice-system; do
    PROJECT_DIR="$REPO_DIR/python-scripts/$PROJECT"
    VENV_DIR="$PROJECT_DIR/venv"

    if [ ! -d "$VENV_DIR" ]; then
        echo "  Creating venv for $PROJECT..."
        python3 -m venv "$VENV_DIR"
    else
        echo "  venv already exists for $PROJECT, skipping."
    fi

    echo "  Installing requirements for $PROJECT..."
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    "$VENV_DIR/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"
    echo "  $PROJECT — done."
done

# ── 4. Move credentials from /tmp to project folders ──────────────────────
echo ""
echo "[4/6] Moving credentials from /tmp..."

move_file() {
    local src="$1"
    local dst="$2"
    if [ -f "$src" ]; then
        mv "$src" "$dst"
        chmod 600 "$dst"
        echo "  Moved $src → $dst"
    else
        echo "  WARNING: $src not found — upload it with SCP before starting services."
    fi
}

move_file /tmp/ea-credentials.json  "$REPO_DIR/python-scripts/email-agent/credentials.json"
move_file /tmp/ea-token.json        "$REPO_DIR/python-scripts/email-agent/token.json"
move_file /tmp/inv-credentials.json "$REPO_DIR/python-scripts/invoice-system/credentials.json"
move_file /tmp/inv-token.json       "$REPO_DIR/python-scripts/invoice-system/token.json"
move_file /tmp/mb-credentials.json  "$REPO_DIR/python-scripts/morning-briefing/credentials.json"
move_file /tmp/mb-token.json        "$REPO_DIR/python-scripts/morning-briefing/token.json"

# ── 5. Create .env templates (only if .env doesn't already exist) ──────────
echo ""
echo "[5/6] Creating .env templates..."

create_env_template() {
    local path="$1"
    local content="$2"
    if [ ! -f "$path" ]; then
        echo "$content" > "$path"
        chmod 600 "$path"
        echo "  Created $path"
    else
        echo "  $path already exists — skipping."
    fi
}

create_env_template "$REPO_DIR/python-scripts/email-agent/.env" \
"ANTHROPIC_API_KEY=
SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
SLACK_USER_ID=
GMAIL_CREDENTIALS_PATH=credentials.json"

create_env_template "$REPO_DIR/python-scripts/morning-briefing/.env" \
"ANTHROPIC_API_KEY=
SLACK_BOT_TOKEN=
SLACK_USER_ID=
INVOICE_SHEET_ID=1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw
ANALYTICS_SHEET_ID=19xls01LAgXzhwR970geSjABFtWTd1GhQ6-goBLv6FMI
EMAIL_AGENT_DIR=/root/my-project/python-scripts/email-agent
GOOGLE_CREDENTIALS_PATH=credentials.json"

create_env_template "$REPO_DIR/python-scripts/invoice-system/.env" \
"ANTHROPIC_API_KEY=
GOOGLE_SHEET_ID=1saaYuyPdpb1BOUZJWKg4AwOgu8LU1C9ThkcnC4zpdGw
GMAIL_CREDENTIALS_PATH=credentials.json"

# ── 6. Install systemd services ────────────────────────────────────────────
echo ""
echo "[6/6] Installing systemd services..."

for SERVICE in email-agent morning-briefing invoice-scan; do
    cp "$DEPLOY_DIR/$SERVICE.service" "/etc/systemd/system/$SERVICE.service"
    echo "  Installed $SERVICE.service"
done

systemctl daemon-reload

for SERVICE in email-agent morning-briefing invoice-scan; do
    systemctl enable "$SERVICE"
    echo "  Enabled $SERVICE (will auto-start on reboot)"
done

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "NEXT STEPS:"
echo ""
echo "  1. Fill in your API keys and tokens in each .env file:"
echo "     nano $REPO_DIR/python-scripts/email-agent/.env"
echo "     nano $REPO_DIR/python-scripts/morning-briefing/.env"
echo "     nano $REPO_DIR/python-scripts/invoice-system/.env"
echo ""
echo "  2. Once .env files are filled, start the services:"
echo "     systemctl start email-agent"
echo "     systemctl start morning-briefing"
echo "     systemctl start invoice-scan"
echo ""
echo "  3. Check status:"
echo "     systemctl status email-agent"
echo "     systemctl status morning-briefing"
echo "     systemctl status invoice-scan"
echo ""
echo "  4. Watch logs live:"
echo "     journalctl -u email-agent -f"
echo "     journalctl -u morning-briefing -f"
echo ""
