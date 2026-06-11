# Deploy to Google Cloud Run — Exact Steps

---

## Before you start — one important note

Cloud Run can run multiple container instances in parallel.
This game keeps all state in memory, so **you must set max-instances=1**.
If two instances run simultaneously, agents will hit different game states.
The commands below enforce this.

---

## What you need

| Requirement | Notes |
|-------------|-------|
| Google account | console.cloud.google.com |
| Google Cloud project | free to create |
| Billing enabled | required for Cloud Run (free tier covers ~2M requests/month) |
| Docker Desktop | installed and running on your local machine |
| Google Cloud SDK (`gcloud`) | installation steps below |

---

## Step 1 — Install Google Cloud SDK

### Windows

1. Download the installer from:
   https://cloud.google.com/sdk/docs/install-sdk#windows

2. Run the installer — it adds `gcloud` to your PATH automatically.

3. Open a new PowerShell window and verify:
   ```powershell
   gcloud --version
   # Google Cloud SDK 470.x.x
   ```

---

## Step 2 — Authenticate and set up your project

Open PowerShell and run each command one at a time:

```powershell
# Log in to Google (opens a browser window)
gcloud auth login

# List your projects to find the project ID
gcloud projects list

# Set the project you want to deploy to
# Replace YOUR_PROJECT_ID with the ID from the list above
gcloud config set project YOUR_PROJECT_ID

# Confirm it's set
gcloud config get project
# Should print: YOUR_PROJECT_ID
```

**If you don't have a project yet:**
```powershell
# Create a new project (project IDs must be globally unique)
gcloud projects create soccer-pitch-2026 --name="Soccer Pitch 2026"
gcloud config set project soccer-pitch-2026

# Enable billing on the project (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
# Link a billing account to soccer-pitch-2026
```

---

## Step 3 — Enable required Google Cloud APIs

```powershell
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

Each command takes about 30 seconds. You'll see:
```
Operation "operations/acf.xxx" finished successfully.
```

---

## Step 4 — Create an Artifact Registry repository

This is where your Docker image will be stored in Google's infrastructure.

```powershell
# Create the repository (run once — skip if it already exists)
gcloud artifacts repositories create soccer-pitch-repo `
    --repository-format=docker `
    --location=us-central1 `
    --description="Soccer Pitch container images"
```

Verify it was created:
```powershell
gcloud artifacts repositories list --location=us-central1
```

---

## Step 5 — Authenticate Docker with Google Cloud

This lets Docker push images to Artifact Registry:

```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev
```

You'll see:
```
Adding credentials for: us-central1-docker.pkg.dev
Docker configuration file updated.
```

---

## Step 6 — Build and push the Docker image

Navigate to your project folder:

```powershell
cd "c:\Users\ASUS\Documents\worldcup - cloud\the_soccer_pitch-main"
```

Set your project ID as a variable (makes the commands shorter):

```powershell
$PROJECT_ID = "YOUR_PROJECT_ID"   # replace with your actual project ID
$REGION     = "us-central1"
$IMAGE      = "$REGION-docker.pkg.dev/$PROJECT_ID/soccer-pitch-repo/soccer-pitch:latest"
```

Build the image and tag it for Google's registry:

```powershell
docker build -t $IMAGE .
```

This takes ~2 minutes the first time (downloading base image + installing deps).
Subsequent builds are faster because Docker caches layers.

You should see at the end:
```
=> exporting to image
=> => naming to us-central1-docker.pkg.dev/YOUR_PROJECT_ID/soccer-pitch-repo/soccer-pitch:latest
```

Push the image to Artifact Registry:

```powershell
docker push $IMAGE
```

You'll see the layers uploading:
```
latest: digest: sha256:abc123... size: 1234
```

---

## Step 7 — Deploy to Cloud Run

```powershell
gcloud run deploy soccer-pitch `
    --image=$IMAGE `
    --platform=managed `
    --region=$REGION `
    --port=8000 `
    --allow-unauthenticated `
    --min-instances=1 `
    --max-instances=1 `
    --memory=512Mi `
    --cpu=1 `
    --timeout=3600 `
    --set-env-vars="HOST=0.0.0.0"
```

**What each flag does:**

| Flag | Why |
|------|-----|
| `--port=8000` | Tells Cloud Run which port the app listens on |
| `--allow-unauthenticated` | Makes the URL public (no login required for agents) |
| `--min-instances=1` | Keeps one instance always running (no cold starts) |
| `--max-instances=1` | **Critical** — one game, one state, no split-brain |
| `--memory=512Mi` | Enough for physics engine + FastAPI |
| `--cpu=1` | 1 vCPU for the physics + API threads |
| `--timeout=3600` | 1-hour request timeout (long-lived agent connections) |

Deployment takes about 60–90 seconds. At the end you'll see:

```
Service [soccer-pitch] revision [soccer-pitch-00001-xxx] has been deployed
and is serving 100 percent of traffic.

Service URL: https://soccer-pitch-xxxxxxxxxx-uc.a.run.app
```

**Copy that URL — that's your game server.**

---

## Step 8 — Verify the deployment

```powershell
# Quick health check
$SERVICE_URL = "https://soccer-pitch-xxxxxxxxxx-uc.a.run.app"   # your URL

# Should return JSON with match state
Invoke-WebRequest -Uri "$SERVICE_URL/api/state" | Select-Object -ExpandProperty Content
```

Expected output:
```json
{"match_state":"Waiting","time_left":90.0,"score":{"Red":0,"Blue":0},"ball":{"x":600.0,"y":425.0},"players":{}}
```

Or run the full smoke test:
```powershell
python deploy/smoke_test.py $SERVICE_URL
```

---

## Step 9 — Play the game

1. Open your service URL in a browser:
   ```
   https://soccer-pitch-xxxxxxxxxx-uc.a.run.app/
   ```
   You'll see the FIFA World Cup 2026 dashboard.

2. Click **▶ START MATCH**

3. Connect agents — point them at:
   ```
   https://soccer-pitch-xxxxxxxxxx-uc.a.run.app/api/action
   ```

4. Watch live at:
   ```
   https://soccer-pitch-xxxxxxxxxx-uc.a.run.app/scoreboard
   ```

### Quick test agent (no AI key needed)

Save this as `test_agent.py` and run it on any machine:

```python
import httpx, time

SERVER = "https://soccer-pitch-xxxxxxxxxx-uc.a.run.app"  # your URL
TEAM   = "Red"
POS    = "Striker"

while True:
    try:
        state = httpx.get(f"{SERVER}/api/state", timeout=10).json()
        if state["match_state"] != "Playing":
            print(f"Waiting... ({state['match_state']})")
            time.sleep(1)
            continue

        ball = state["ball"]
        me   = state["players"].get(f"{TEAM}_{POS}", {"x": 600, "y": 425})
        dx   = ball["x"] - me["x"]
        dy   = ball["y"] - me["y"]
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 0:
            dx, dy = dx / dist, dy / dist

        httpx.post(f"{SERVER}/api/action", json={
            "team": TEAM, "position": POS,
            "vector": {"dx": round(dx, 3), "dy": round(dy, 3)},
            "kick": dist < 50,
            "agent_name": "CloudBot",
        }, timeout=10)
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(0.15)
```

---

## Updating after code changes

After changing any source file, rebuild and redeploy:

```powershell
cd "c:\Users\ASUS\Documents\worldcup - cloud\the_soccer_pitch-main"

# Rebuild and push
docker build -t $IMAGE .
docker push $IMAGE

# Redeploy (Cloud Run rolls out the new image with zero downtime)
gcloud run deploy soccer-pitch `
    --image=$IMAGE `
    --platform=managed `
    --region=$REGION
```

Cloud Run keeps the old revision running until the new one is healthy, then switches traffic over.

---

## Useful commands

```powershell
# View live logs
gcloud run services logs tail soccer-pitch --region=$REGION

# Describe the service (URL, env vars, resource limits)
gcloud run services describe soccer-pitch --region=$REGION

# List all revisions
gcloud run revisions list --service=soccer-pitch --region=$REGION

# Roll back to a previous revision
gcloud run services update-traffic soccer-pitch `
    --to-revisions=soccer-pitch-00001-xxx=100 `
    --region=$REGION

# Delete the service (stops billing)
gcloud run services delete soccer-pitch --region=$REGION
```

---

## Cost estimate

Cloud Run free tier (per month, per project):
- **2 million requests** free
- **360,000 vCPU-seconds** free
- **180,000 GB-seconds** memory free

With `--min-instances=1` the container runs continuously.
Outside the free tier: ~$0.05–0.10/day for a 512Mi / 1 vCPU instance.

To stop billing completely:
```powershell
gcloud run services delete soccer-pitch --region=$REGION
```

---

## Troubleshooting

**Deploy fails: "Revision failed to start"**
```powershell
# Check what went wrong
gcloud run services logs tail soccer-pitch --region=$REGION
```
Usually a Python import error or the port isn't listening. Check logs for the traceback.

**"Permission denied" when pushing image**
```powershell
# Re-authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev
```

**Agents can't connect / connection timeout**
- Confirm `--allow-unauthenticated` was set on deploy
- The URL must start with `https://` not `http://`
- Cloud Run only accepts HTTPS — your agents need to use HTTPS too

**Game state resets unexpectedly**
- Confirm `--max-instances=1` — if it was deployed without this flag, redeploy with it
- Cloud Run may restart the instance after ~60 min idle if `--min-instances=0` — set `--min-instances=1`

**"ERROR: (gcloud.run.deploy) Cloud Run error: Container failed to start"**
Test the image locally first:
```powershell
docker run -p 8000:8000 -e PORT=8000 $IMAGE
# Open http://localhost:8000/api/state
# If it fails locally, it will fail on Cloud Run too
```
