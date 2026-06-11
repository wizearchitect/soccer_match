#!/bin/bash
# VPS Setup Script — full game with virtual display (Xvfb)
# Tested on Ubuntu 22.04 LTS
# Run as: bash vps_setup.sh

set -e  # exit on any error

echo "=== The Pitch — VPS Setup ==="

# ── System packages ───────────────────────────────────────────────────────────
echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3.11 python3.11-venv python3-pip \
    xvfb \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportaudio2 \
    git \
    curl

# ── Clone repo (skip if already present) ─────────────────────────────────────
echo "[2/6] Setting up project..."
REPO_DIR="$HOME/the_soccer_pitch"
if [ ! -d "$REPO_DIR" ]; then
    echo "  Cloning repository..."
    git clone https://github.com/YOUR_USERNAME/the_soccer_pitch-main.git "$REPO_DIR"
else
    echo "  Repo already present, pulling latest..."
    git -C "$REPO_DIR" pull
fi

# ── Python virtual environment ────────────────────────────────────────────────
echo "[3/6] Creating Python virtual environment..."
cd "$REPO_DIR/pitch"
python3.11 -m venv soccer_a
source soccer_a/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# ── systemd service: Xvfb virtual display ────────────────────────────────────
echo "[4/6] Installing Xvfb systemd service..."
sudo tee /etc/systemd/system/xvfb.service > /dev/null <<'SERVICE'
[Unit]
Description=Virtual Framebuffer (Xvfb) for The Pitch
Before=pitch.service

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1200x800x24 -nolisten tcp
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

# ── systemd service: The Pitch ────────────────────────────────────────────────
echo "[5/6] Installing Pitch systemd service..."
PYTHON_PATH="$REPO_DIR/pitch/soccer_a/bin/python"
sudo tee /etc/systemd/system/pitch.service > /dev/null <<SERVICE
[Unit]
Description=The Soccer Pitch Game Server
After=network.target xvfb.service
Requires=xvfb.service

[Service]
User=$USER
WorkingDirectory=$REPO_DIR
Environment=DISPLAY=:99
Environment=HOST=0.0.0.0
Environment=PORT=8000
ExecStart=$PYTHON_PATH -m pitch.main
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# ── Firewall rule ─────────────────────────────────────────────────────────────
echo "[6/6] Opening firewall port 8000..."
sudo ufw allow 8000/tcp 2>/dev/null || true

# ── Enable and start services ─────────────────────────────────────────────────
sudo systemctl daemon-reload
sudo systemctl enable xvfb.service
sudo systemctl enable pitch.service
sudo systemctl start xvfb.service
sleep 2
sudo systemctl start pitch.service

echo ""
echo "=== Setup complete ==="
echo ""
echo "Services started:"
echo "  sudo systemctl status pitch"
echo "  sudo journalctl -u pitch -f"
echo ""
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "<your-vps-ip>")
echo "Dashboard  : http://$PUBLIC_IP:8000/"
echo "Scoreboard : http://$PUBLIC_IP:8000/scoreboard"
echo "API state  : http://$PUBLIC_IP:8000/api/state"
echo ""
echo "Match control: use the dashboard — no keyboard/spacebar needed!"
