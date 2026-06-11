#!/bin/bash
# VPS Setup Script — headless mode (no display required)
# Tested on Ubuntu 22.04 LTS
# Run as: bash vps_headless.sh

set -e

echo "=== The Pitch — Headless VPS Setup ==="

# ── System packages ───────────────────────────────────────────────────────────
echo "[1/5] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3.11 python3.11-venv python3-pip \
    git curl

# ── Clone repo ────────────────────────────────────────────────────────────────
echo "[2/5] Setting up project..."
REPO_DIR="$HOME/the_soccer_pitch"
if [ ! -d "$REPO_DIR" ]; then
    git clone https://github.com/YOUR_USERNAME/the_soccer_pitch-main.git "$REPO_DIR"
else
    git -C "$REPO_DIR" pull
fi

# ── Virtual environment ───────────────────────────────────────────────────────
echo "[3/5] Creating Python virtual environment..."
cd "$REPO_DIR/pitch"
python3.11 -m venv soccer_a
source soccer_a/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements_headless.txt

# ── systemd service ───────────────────────────────────────────────────────────
echo "[4/5] Installing systemd service..."
PYTHON_PATH="$REPO_DIR/pitch/soccer_a/bin/python"
sudo tee /etc/systemd/system/pitch.service > /dev/null <<SERVICE
[Unit]
Description=The Soccer Pitch (Headless)
After=network.target

[Service]
User=$USER
WorkingDirectory=$REPO_DIR
Environment=HOST=0.0.0.0
Environment=PORT=8000
ExecStart=$PYTHON_PATH -m pitch.main_headless
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# ── Firewall ──────────────────────────────────────────────────────────────────
echo "[5/5] Opening firewall port 8000..."
sudo ufw allow 8000/tcp 2>/dev/null || true

sudo systemctl daemon-reload
sudo systemctl enable pitch.service
sudo systemctl start pitch.service

echo ""
echo "=== Setup complete ==="
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "<your-vps-ip>")
echo "Dashboard  : http://$PUBLIC_IP:8000/"
echo "Scoreboard : http://$PUBLIC_IP:8000/scoreboard"
echo "Logs       : sudo journalctl -u pitch -f"
