# Docker VPS Deployment — Step by Step

Deploy the Soccer Pitch server to any VPS running Ubuntu 22.04.
Total time: ~10 minutes on a fresh VPS.

---

## What you need

| Item | Where to get |
|------|-------------|
| VPS (1 vCPU, 1 GB RAM minimum) | DigitalOcean / Hetzner / Vultr / Linode |
| Ubuntu 22.04 LTS | Select when creating the droplet/server |
| Your repo on GitHub | github.com/you/the_soccer_pitch-main |
| SSH access to the VPS | Provided by your VPS provider |

> Cheapest option: Hetzner CX11 (~€4/month) or DigitalOcean Basic ($6/month)

---

## Part 1 — Provision the VPS

### DigitalOcean (example)

1. Log in → **Create** → **Droplets**
2. Choose:
   - Image: **Ubuntu 22.04 LTS**
   - Size: **Basic — Shared CPU — Regular — 1 GB / 1 vCPU** ($6/mo)
   - Region: closest to your players
   - Authentication: **SSH Key** (recommended) or password
3. Click **Create Droplet**
4. Copy the droplet's **IPv4 address** (e.g. `159.65.12.34`)

### Hetzner (alternative, cheaper)

1. Log in → **Servers** → **Add Server**
2. Image: **Ubuntu 22.04**, Type: **CX11** (€4/mo)
3. Add your SSH key → **Create & Buy**

---

## Part 2 — Install Docker on the VPS

SSH into your new server:

```bash
ssh root@<YOUR_VPS_IP>
```

Run these commands one by one:

```bash
# 1. Update packages
apt-get update && apt-get upgrade -y

# 2. Install Docker (official script — quickest method)
curl -fsSL https://get.docker.com | sh

# 3. Verify Docker installed correctly
docker --version
# Expected: Docker version 25.x.x, build ...

# 4. Install Docker Compose plugin
apt-get install -y docker-compose-plugin

# 5. Verify Compose
docker compose version
# Expected: Docker Compose version v2.x.x

# 6. (Optional but recommended) Add a non-root user
adduser deploy
usermod -aG docker deploy
# Now you can SSH as 'deploy' and run docker without sudo
```

---

## Part 3 — Copy your code to the VPS

**Option A — Git clone (recommended)**

```bash
# On the VPS
apt-get install -y git

git clone https://github.com/YOUR_USERNAME/the_soccer_pitch-main.git
cd the_soccer_pitch-main
```

**Option B — rsync from your local machine**

```bash
# Run this on your LOCAL machine (Windows: use Git Bash or WSL)
rsync -avz \
  --exclude='.git' \
  --exclude='**/soccer_a' \
  --exclude='**/__pycache__' \
  --exclude='**/.env' \
  "c:/Users/ASUS/Documents/worldcup - cloud/the_soccer_pitch-main/" \
  root@<YOUR_VPS_IP>:/root/the_soccer_pitch-main/
```

**Option C — SCP from Windows (PowerShell)**

```powershell
# Run in PowerShell on your local machine
scp -r "c:\Users\ASUS\Documents\worldcup - cloud\the_soccer_pitch-main" `
    root@<YOUR_VPS_IP>:/root/
```

---

## Part 4 — Build and Run with Docker

```bash
# On the VPS — inside the project folder
cd /root/the_soccer_pitch-main

# Build the image (~60 seconds on first run, cached after)
docker build -t soccer-pitch:latest .

# Verify the image was built
docker images soccer-pitch
# REPOSITORY     TAG       IMAGE ID       SIZE
# soccer-pitch   latest    abc123...      ~120MB
```

### Run it

```bash
# Start the container (detached, auto-restarts on crash/reboot)
docker compose up -d

# Check it started cleanly
docker compose ps
# NAME            STATUS
# soccer-pitch    Up 30 seconds (healthy)

# Follow live logs
docker compose logs -f
```

You should see:
```
============================================================
  The Pitch — Headless / Cloud Mode
  Local IP  : 172.17.0.2
  Binding   : 0.0.0.0:8000
  Dashboard : http://172.17.0.2:8000/
  Scoreboard: http://172.17.0.2:8000/scoreboard
============================================================
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Part 5 — Open the Firewall

```bash
# Allow port 8000 through the VPS firewall
ufw allow 8000/tcp
ufw enable    # if not already enabled
ufw status
```

Also check your VPS provider's dashboard:
- **DigitalOcean**: Go to your Droplet → Networking → Firewall → add inbound rule TCP 8000
- **Hetzner**: Server → Firewalls → add inbound TCP 8000

---

## Part 6 — Verify it's working

From your **local machine** (not the VPS):

```bash
# Quick check — should return JSON
curl http://<YOUR_VPS_IP>:8000/api/state

# Full smoke test (20 checks)
python deploy/smoke_test.py http://<YOUR_VPS_IP>:8000
```

Open in your browser:
- **Dashboard**: `http://<YOUR_VPS_IP>:8000/`
- **Scoreboard**: `http://<YOUR_VPS_IP>:8000/scoreboard`

---

## Part 7 — Play the Game

1. Open `http://<YOUR_VPS_IP>:8000/` in your browser
2. Click **▶ START MATCH** to begin a 90-second match
3. Connect agents by pointing them at:
   ```
   http://<YOUR_VPS_IP>:8000/api/action
   ```
4. Watch the scoreboard at `http://<YOUR_VPS_IP>:8000/scoreboard`
5. Use **⏮ RESET MATCH** or **🏁 END MATCH** from the dashboard

### Quick test agent (no AI key needed)

Run this on any machine that can reach the VPS:

```python
# test_agent.py
import httpx, time, random

SERVER = "http://<YOUR_VPS_IP>:8000"
TEAM   = "Red"    # change to "Blue" for second agent
POS    = "Striker"

print(f"Connecting to {SERVER} as {TEAM} {POS}...")

while True:
    try:
        state = httpx.get(f"{SERVER}/api/state", timeout=5).json()

        if state["match_state"] != "Playing":
            print(f"  Waiting for match to start... ({state['match_state']})")
            time.sleep(1)
            continue

        ball = state["ball"]
        me   = state["players"].get(f"{TEAM}_{POS}", {"x": 600, "y": 425})

        # Move toward the ball
        dx = ball["x"] - me["x"]
        dy = ball["y"] - me["y"]
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 0:
            dx, dy = dx / dist, dy / dist

        httpx.post(f"{SERVER}/api/action", json={
            "team": TEAM,
            "position": POS,
            "vector": {"dx": round(dx, 3), "dy": round(dy, 3)},
            "kick": dist < 50,
            "agent_name": f"TestBot-{TEAM}",
        }, timeout=5)

    except Exception as e:
        print(f"  Error: {e}")

    time.sleep(0.15)
```

Run two terminals with `TEAM = "Red"` and `TEAM = "Blue"` to watch both sides play.

---

## Day-2 Operations

### Update the server after code changes

```bash
# On the VPS
cd /root/the_soccer_pitch-main
git pull                          # pull latest code
docker compose down               # stop the container
docker build -t soccer-pitch:latest .   # rebuild
docker compose up -d              # start again
docker compose logs -f            # verify clean startup
```

### Change the port

```bash
# On the VPS — edit docker-compose.yml or use env override
PORT=9000 docker compose up -d
```

### View logs without following

```bash
docker compose logs --tail=100
```

### Stop the server

```bash
docker compose down
```

### Restart the server

```bash
docker compose restart
```

### Check health status

```bash
docker inspect --format='{{.State.Health.Status}}' soccer-pitch
# healthy
```

### Free disk space (remove old images)

```bash
docker image prune -f
```

---

## Troubleshooting

**Container exits immediately after starting**
```bash
docker compose logs
```
Usually a missing import or port conflict. Check logs for the error.

**Port 8000 refused / can't connect from outside**
```bash
# Confirm container is running
docker compose ps

# Confirm port is bound on the VPS
ss -tlnp | grep 8000

# Confirm firewall allows it
ufw status | grep 8000
```

**Health check failing (container shows 'unhealthy')**
```bash
docker inspect soccer-pitch | grep -A 5 Health
# Usually means the app crashed — check logs
docker compose logs --tail=50
```

**Out of memory**
```bash
free -h
docker stats --no-stream
# If memory is tight, reduce PHYSICS_TICK_RATE in config.py or upgrade to 2GB VPS
```

---

## Security Hardening (optional)

```bash
# 1. Put Nginx in front for HTTPS (Let's Encrypt)
apt-get install -y nginx certbot python3-certbot-nginx

# Point your domain (e.g. pitch.example.com) A-record to the VPS IP
# Then:
certbot --nginx -d pitch.example.com

# Nginx proxy config (/etc/nginx/sites-available/pitch):
# server {
#     listen 443 ssl;
#     server_name pitch.example.com;
#     location / {
#         proxy_pass http://localhost:8000;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#     }
# }

# 2. Restrict port 8000 to localhost only (once Nginx is in front)
# In docker-compose.yml, change:
#   ports:
#     - "8000:8000"          # public
# to:
#     - "127.0.0.1:8000:8000"  # localhost only
```
