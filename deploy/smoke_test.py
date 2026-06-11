"""
Smoke test suite for a deployed Pitch server.

Usage:
    python deploy/smoke_test.py http://<your-server>:8000

Requires only stdlib + httpx (already in requirements.txt).
Runs 10 checks against a live server and prints PASS/FAIL for each.
"""

import sys
import json
import time

try:
    import httpx
except ImportError:
    sys.exit("httpx not installed. Run: pip install httpx")

# ── Config ────────────────────────────────────────────────────────────────────
BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
TIMEOUT = 10.0
PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"

results = []

def check(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  {status}  {name}{suffix}")
    results.append(passed)

print(f"\n{'='*55}")
print(f"  Smoke Test — {BASE}")
print(f"{'='*55}\n")

client = httpx.Client(base_url=BASE, timeout=TIMEOUT)

# ── 1. Dashboard loads ────────────────────────────────────────────────────────
try:
    r = client.get("/")
    check("Dashboard / returns 200", r.status_code == 200)
    check("Dashboard contains FIFA branding",
          "FIFA WORLD CUP 2026" in r.text or "Football Soccer" in r.text)
except Exception as e:
    check("Dashboard / returns 200", False, str(e))
    check("Dashboard contains FIFA branding", False)

# ── 2. GET /api/state schema ──────────────────────────────────────────────────
try:
    r = client.get("/api/state")
    check("GET /api/state returns 200", r.status_code == 200)
    data = r.json()
    required = {"match_state", "time_left", "score", "ball", "players"}
    missing = required - set(data.keys())
    check("State has all required fields", not missing,
          f"missing: {missing}" if missing else "")
    check("match_state is Waiting or Playing",
          data.get("match_state") in ("Waiting", "Playing"))
    check("time_left is numeric", isinstance(data.get("time_left"), (int, float)))
    check("score has Red and Blue", set(data.get("score", {}).keys()) == {"Red", "Blue"})
    check("ball has x and y", "x" in data.get("ball", {}) and "y" in data.get("ball", {}))
except Exception as e:
    for _ in range(6):
        check("API state check", False, str(e))

# ── 3. POST /api/action spawns a player ──────────────────────────────────────
try:
    r = client.post("/api/action", json={
        "team": "Red",
        "position": "Striker",
        "vector": {"dx": 0.0, "dy": 0.0},
        "kick": False,
        "agent_name": "SmokeTest",
    })
    check("POST /api/action returns 200", r.status_code == 200)
    d = r.json()
    check("Action response has status ok", d.get("status") == "ok")
    check("Player name in response", d.get("player") == "Red_Striker")
except Exception as e:
    for _ in range(3):
        check("POST /api/action", False, str(e))

# ── 4. Match control endpoints ────────────────────────────────────────────────
try:
    r = client.post("/api/match/start")
    check("POST /api/match/start returns 200", r.status_code == 200)
except Exception as e:
    check("POST /api/match/start returns 200", False, str(e))

try:
    r = client.post("/api/match/reset-ball")
    check("POST /api/match/reset-ball returns 200", r.status_code == 200)
except Exception as e:
    check("POST /api/match/reset-ball returns 200", False, str(e))

try:
    r = client.post("/api/match/end")
    check("POST /api/match/end returns 200", r.status_code == 200)
except Exception as e:
    check("POST /api/match/end returns 200", False, str(e))

try:
    r = client.post("/api/match/reset-match")
    check("POST /api/match/reset-match returns 200", r.status_code == 200)
except Exception as e:
    check("POST /api/match/reset-match returns 200", False, str(e))

# ── 5. Scoreboard ─────────────────────────────────────────────────────────────
try:
    r = client.get("/scoreboard")
    check("GET /scoreboard returns 200", r.status_code == 200)
    check("Scoreboard contains FIFA branding",
          "FIFA" in r.text or "Scoreboard" in r.text)
except Exception as e:
    for _ in range(2):
        check("Scoreboard check", False, str(e))

try:
    r = client.get("/api/scoreboard")
    check("GET /api/scoreboard JSON returns 200", r.status_code == 200)
    sb = r.json()
    check("Scoreboard JSON has red_goals and blue_goals",
          "red_goals" in sb and "blue_goals" in sb)
except Exception as e:
    for _ in range(2):
        check("Scoreboard JSON check", False, str(e))

# ── 6. Invalid team rejected ──────────────────────────────────────────────────
try:
    r = client.post("/api/action", json={
        "team": "Purple",
        "position": "Striker",
        "vector": {"dx": 0.0, "dy": 0.0},
        "kick": False,
    })
    check("Invalid team returns 400", r.status_code == 400)
except Exception as e:
    check("Invalid team returns 400", False, str(e))

client.close()

# ── Summary ───────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'='*55}")
print(f"  Result: {passed}/{total} checks passed")
if passed == total:
    print("  \033[92mAll checks PASSED — server is healthy.\033[0m")
else:
    print(f"  \033[91m{total - passed} check(s) FAILED.\033[0m")
print(f"{'='*55}\n")

sys.exit(0 if passed == total else 1)
