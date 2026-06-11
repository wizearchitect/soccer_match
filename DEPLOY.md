# Deployment Guide — The Soccer Pitch

Three deployment paths, from quickest to most control.

---

## Option A — Railway (Quickest, free tier)

**Time to live: ~3 minutes**

1. Push your repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo — Railway auto-detects `railway.toml` and runs:
   ```
   pip install -r pitch/requirements_headless.txt
   python -m pitch.main_headless
   ```
4. Railway assigns a public HTTPS URL automatically (e.g. `https://the-soccer-pitch.up.railway.app`)
5. No env vars needed — `PORT` is injected automatically

**Test it:**
```bash
python deploy/smoke_test.py https://the-soccer-pitch.up.railway.app
```

---

## Option B — Render (Free tier, auto-sleep)

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → Connect repo
3. Render reads `render.yaml` automatically, or set manually:
   - **Build command:** `pip install -r pitch/requirements_headless.txt`
   - **Start command:** `python -m pitch.main_headless`
4. Deploy — get a URL like `https://the-soccer-pitch.onrender.com`

> ⚠️ Free tier spins down after 15 min idle. First request after sleep takes ~30s.

---

## Option C — VPS with full PyGame display (DigitalOcean / Hetzner / Vultr)

**Best for a live tournament — game stays up, full audio, full renderer.**

Cost: ~$6/month (2GB RAM droplet)

```bash
# 1. SSH into your new VPS
ssh ubuntu@<your-vps-ip>

# 2. Download and run the setup script
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/the_soccer_pitch-main/main/deploy/vps_setup.sh
bash vps_setup.sh
```

The script installs Xvfb (virtual display), creates a systemd service, and
opens port 8000. The full PyGame renderer runs invisibly on Xvfb.

**Useful commands after setup:**
```bash
sudo systemctl status pitch          # Check if running
sudo journalctl -u pitch -f          # Live logs
sudo systemctl restart pitch         # Restart after code changes
```

---

## Option D — Docker (Any Docker host)

Build and run locally:
```bash
docker build -t soccer-pitch .
docker run -p 8000:8000 soccer-pitch
```

Deploy to any Docker host (Fly.io, ECS, Cloud Run, etc.):
```bash
# Fly.io
fly launch    # first time — reads fly.toml
fly deploy    # subsequent deploys

# Google Cloud Run
gcloud run deploy soccer-pitch \
  --source . \
  --port 8000 \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Testing a Deployed Server

Run the smoke test against any live URL:

```bash
# Local
python deploy/smoke_test.py http://localhost:8000

# Railway
python deploy/smoke_test.py https://the-soccer-pitch.up.railway.app

# VPS
python deploy/smoke_test.py http://123.45.67.89:8000
```

The smoke test checks 20 endpoints and prints PASS/FAIL for each.

---

## Playing the Game After Deployment

1. **Open the dashboard:** `https://<your-url>/`
2. **Click START MATCH** — no spacebar needed in headless mode
3. **Connect agents** — point them at `https://<your-url>/api/action`
4. **Watch the scoreboard:** `https://<your-url>/scoreboard`

### Quick agent test (no NVIDIA key needed)

```python
import httpx, time, random

SERVER = "https://your-url"

while True:
    state = httpx.get(f"{SERVER}/api/state", timeout=5).json()
    if state["match_state"] != "Playing":
        time.sleep(1)
        continue

    httpx.post(f"{SERVER}/api/action", json={
        "team": "Red",
        "position": "Striker",
        "vector": {"dx": random.uniform(-1, 1), "dy": random.uniform(-1, 1)},
        "kick": True,
        "agent_name": "TestBot",
    }, timeout=5)
    time.sleep(0.2)
```

---

## Environment Variables Reference

| Variable | Default | Where to set |
|----------|---------|--------------|
| `HOST`   | `0.0.0.0` | `.env` or platform env vars |
| `PORT`   | `8000`    | Injected automatically by Railway/Render/Fly |

No API keys are required for the pitch server itself. Only the `player/` and
`team/` agent clients need `NVIDIA_API_KEY`.

---

## Headless vs Full Mode

| Feature | Headless (`main_headless.py`) | Full (`main.py`) |
|---------|-------------------------------|------------------|
| PyGame window | ✗ | ✓ |
| Audio (goal sound) | ✗ | ✓ |
| Web dashboard at `/` | ✓ | ✓ |
| REST API | ✓ | ✓ |
| Physics engine | ✓ | ✓ |
| Match control | Dashboard / API | Spacebar + Dashboard |
| Cloud deployable | ✓ | VPS only (needs Xvfb) |
| `pygame` required | ✗ | ✓ |
