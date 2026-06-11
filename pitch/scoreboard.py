"""Scoreboard module for The Pitch.

Provides a web-based scoreboard page at /scoreboard showing goal events
per team, top scorers, and a download button for markdown export.
"""

from collections import Counter

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from pitch.state import StateManager

router = APIRouter()

# Module-level state manager reference, set by main.py
state_manager: StateManager = None  # type: ignore


def _get_scoreboard_data() -> dict:
    """Read goal log from state and build scoreboard data.

    If the current match has no goals (e.g., just reset), shows the
    previous match data so it can still be downloaded.

    Returns a dict with red_goals, blue_goals lists and top_scorers per team.
    """
    if not state_manager.acquire(timeout=2.0):
        return {"red_goals": [], "blue_goals": [], "red_top": [], "blue_top": [], "score": {"Red": 0, "Blue": 0}, "is_previous": False}

    try:
        state = state_manager.state
        score = dict(state.score)
        goal_log = state.goal_log
        is_previous = False

        # If current match has no goals, show previous match data
        if not goal_log and state_manager.previous_match:
            score = state_manager.previous_match["score"]
            goal_log = state_manager.previous_match["goal_log"]
            is_previous = True

        red_goals = []
        blue_goals = []

        for event in goal_log:
            entry = {
                "time": f"{event.time:.1f}s",
                "scorer": event.scorer,
            }
            if event.team == "Red":
                red_goals.append(entry)
            else:
                blue_goals.append(entry)

        # Compute top scorers per team
        red_scorers = Counter(e.scorer for e in goal_log if e.team == "Red")
        blue_scorers = Counter(e.scorer for e in goal_log if e.team == "Blue")

        red_top = [{"name": name, "goals": count} for name, count in red_scorers.most_common()]
        blue_top = [{"name": name, "goals": count} for name, count in blue_scorers.most_common()]

        return {
            "red_goals": red_goals,
            "blue_goals": blue_goals,
            "red_top": red_top,
            "blue_top": blue_top,
            "score": score,
            "is_previous": is_previous,
        }
    finally:
        state_manager.release()


@router.get("/api/scoreboard")
async def get_scoreboard_json() -> JSONResponse:
    """Return scoreboard data as JSON."""
    data = _get_scoreboard_data()
    return JSONResponse(status_code=200, content=data)


@router.get("/api/scoreboard/download")
async def download_scoreboard_md() -> PlainTextResponse:
    """Return scoreboard as downloadable markdown."""
    data = _get_scoreboard_data()
    md = _build_markdown(data)
    return PlainTextResponse(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=scoreboard.md"},
    )


@router.get("/scoreboard")
async def scoreboard_page() -> HTMLResponse:
    """Serve the scoreboard HTML page."""
    return HTMLResponse(content=SCOREBOARD_HTML)


def _build_markdown(data: dict) -> str:
    """Build a markdown string from scoreboard data."""
    lines = []
    lines.append("# Match Scoreboard")
    lines.append("")
    lines.append(f"**Red {data['score'].get('Red', 0)} - {data['score'].get('Blue', 0)} Blue**")
    lines.append("")

    # Red team goals
    lines.append("## Red Team Goals")
    lines.append("")
    if data["red_goals"]:
        lines.append("| Goal Time | Agent Name |")
        lines.append("|-----------|------------|")
        for g in data["red_goals"]:
            lines.append(f"| {g['time']} | {g['scorer']} |")
    else:
        lines.append("_No goals scored._")
    lines.append("")

    # Blue team goals
    lines.append("## Blue Team Goals")
    lines.append("")
    if data["blue_goals"]:
        lines.append("| Goal Time | Agent Name |")
        lines.append("|-----------|------------|")
        for g in data["blue_goals"]:
            lines.append(f"| {g['time']} | {g['scorer']} |")
    else:
        lines.append("_No goals scored._")
    lines.append("")

    # Top scorers
    lines.append("## Top Scorers")
    lines.append("")
    lines.append("### Red Team")
    lines.append("")
    if data["red_top"]:
        lines.append("| Agent Name | Goals |")
        lines.append("|------------|-------|")
        for s in data["red_top"]:
            lines.append(f"| {s['name']} | {s['goals']} |")
    else:
        lines.append("_No scorers._")
    lines.append("")

    lines.append("### Blue Team")
    lines.append("")
    if data["blue_top"]:
        lines.append("| Agent Name | Goals |")
        lines.append("|------------|-------|")
        for s in data["blue_top"]:
            lines.append(f"| {s['name']} | {s['goals']} |")
    else:
        lines.append("_No scorers._")
    lines.append("")

    return "\n".join(lines)


SCOREBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Match Scoreboard – FIFA World Cup 2026 Edition</title>
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg: #0d0d0d; --surface: #141414; --surface2: #1a1a1a;
            --border: #2a2a2a; --cyan: #00e5cc; --green: #22c55e;
            --red: #f87171; --blue: #60a5fa; --text: #e5e5e5;
            --text-dim: #737373; --text-muted: #404040; --radius: 6px;
        }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 0;
        }

        /* Header */
        header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 14px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header-title { font-size: 1.1rem; font-weight: 700; color: var(--cyan); }
        .header-sub { font-size: 0.68rem; color: var(--text-dim); letter-spacing: 1.2px; text-transform: uppercase; margin-top: 2px; }
        .back-link {
            font-size: 0.78rem; color: var(--text-dim); text-decoration: none;
            padding: 5px 10px; border: 1px solid var(--border); border-radius: var(--radius);
            transition: color .15s, border-color .15s;
        }
        .back-link:hover { color: var(--cyan); border-color: var(--cyan); }

        /* Score hero */
        .score-hero {
            text-align: center;
            padding: 28px 20px 20px;
        }
        .score-teams {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 24px;
            margin-bottom: 10px;
        }
        .score-team-name { font-size: 0.85rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
        .score-team-name.red  { color: var(--red); }
        .score-team-name.blue { color: var(--blue); }
        .score-big { font-size: 3rem; font-weight: 900; letter-spacing: -2px; }
        .score-sep { font-size: 2rem; font-weight: 300; color: var(--text-dim); }
        .prev-badge {
            display: inline-block;
            font-size: 0.68rem;
            background: var(--surface2);
            border: 1px solid var(--border);
            color: var(--text-dim);
            padding: 2px 8px;
            border-radius: 20px;
            margin-top: 6px;
        }

        /* Grid */
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 20px 20px;
        }
        @media (max-width: 640px) { .container { grid-template-columns: 1fr; } }

        .team-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
        }
        .team-panel-header {
            padding: 12px 16px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            border-bottom: 1px solid var(--border);
        }
        .team-panel.red  .team-panel-header { color: var(--red);  border-bottom-color: var(--red); }
        .team-panel.blue .team-panel-header { color: var(--blue); border-bottom-color: var(--blue); }

        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 9px 16px; text-align: left; }
        th {
            background: var(--surface2);
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-dim);
            border-bottom: 1px solid var(--border);
        }
        td { font-size: 0.82rem; border-bottom: 1px solid var(--border); }
        tr:last-child td { border-bottom: none; }
        td.empty { color: var(--text-muted); font-style: italic; }

        .top-scorers {
            padding: 12px 16px;
            border-top: 1px solid var(--border);
        }
        .top-scorers-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--text-dim);
            margin-bottom: 8px;
        }
        .scorer-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 0.8rem;
        }
        .scorer-goals {
            font-weight: 700;
            font-size: 0.75rem;
            padding: 2px 7px;
            border-radius: 20px;
            background: var(--surface2);
            border: 1px solid var(--border);
        }
        .scorer-empty { color: var(--text-muted); font-style: italic; font-size: 0.78rem; }

        /* Download bar */
        .actions-bar {
            text-align: center;
            padding: 16px 20px 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        .download-btn {
            background: var(--surface);
            color: var(--text);
            border: 1px solid var(--border);
            padding: 9px 20px;
            border-radius: var(--radius);
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: border-color .15s, color .15s;
        }
        .download-btn:hover { border-color: var(--cyan); color: var(--cyan); }
        .auto-refresh { color: var(--text-muted); font-size: 0.72rem; }
        .live-dot {
            display: inline-block;
            width: 7px; height: 7px;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 5px var(--green);
            margin-right: 4px;
        }
    </style>
</head>
<body>

<header>
    <div>
        <div class="header-title">⚽ Match Scoreboard</div>
        <div class="header-sub">vs FIFA World Cup 2026 &middot; USA &middot; Canada &middot; Mexico</div>
    </div>
    <a class="back-link" href="/">← Control Panel</a>
</header>

<div class="score-hero">
    <div class="score-teams">
        <span class="score-team-name red">Red</span>
        <div>
            <span class="score-big" id="score-red" style="color:var(--red)">0</span>
            <span class="score-sep"> – </span>
            <span class="score-big" id="score-blue" style="color:var(--blue)">0</span>
        </div>
        <span class="score-team-name blue">Blue</span>
    </div>
    <div id="prev-badge" style="display:none;" class="prev-badge">Previous Match</div>
</div>

<div class="container">
    <div class="team-panel red">
        <div class="team-panel-header">🔴 Red Team Goals</div>
        <table>
            <thead><tr><th>Time</th><th>Scorer</th></tr></thead>
            <tbody id="red-goals"><tr><td colspan="2" class="empty">No goals yet</td></tr></tbody>
        </table>
        <div class="top-scorers">
            <div class="top-scorers-label">Top Scorers</div>
            <div id="red-top"><div class="scorer-empty">—</div></div>
        </div>
    </div>
    <div class="team-panel blue">
        <div class="team-panel-header">🔵 Blue Team Goals</div>
        <table>
            <thead><tr><th>Time</th><th>Scorer</th></tr></thead>
            <tbody id="blue-goals"><tr><td colspan="2" class="empty">No goals yet</td></tr></tbody>
        </table>
        <div class="top-scorers">
            <div class="top-scorers-label">Top Scorers</div>
            <div id="blue-top"><div class="scorer-empty">—</div></div>
        </div>
    </div>
</div>

<div class="actions-bar">
    <a class="download-btn" href="/api/scoreboard/download">⬇ Download Markdown</a>
    <span class="auto-refresh"><span class="live-dot"></span>Live · refreshes every 2s</span>
</div>

<script>
    async function refresh() {
        try {
            const res = await fetch('/api/scoreboard');
            const data = await res.json();
            updateUI(data);
        } catch (e) { /* ignore */ }
    }

    function updateUI(data) {
        document.getElementById('score-red').textContent  = data.score.Red  ?? 0;
        document.getElementById('score-blue').textContent = data.score.Blue ?? 0;
        document.getElementById('prev-badge').style.display = data.is_previous ? '' : 'none';

        setGoals('red-goals',  data.red_goals);
        setGoals('blue-goals', data.blue_goals);
        setTop('red-top',  data.red_top);
        setTop('blue-top', data.blue_top);
    }

    function setGoals(id, goals) {
        const el = document.getElementById(id);
        if (goals.length === 0) {
            el.innerHTML = '<tr><td colspan="2" class="empty">No goals yet</td></tr>';
        } else {
            el.innerHTML = goals.map(g =>
                `<tr><td>${g.time}</td><td>${escHtml(g.scorer)}</td></tr>`
            ).join('');
        }
    }

    function setTop(id, top) {
        const el = document.getElementById(id);
        if (top.length === 0) {
            el.innerHTML = '<div class="scorer-empty">—</div>';
        } else {
            el.innerHTML = top.map(s =>
                `<div class="scorer-row"><span>${escHtml(s.name)}</span>
                 <span class="scorer-goals">${s.goals} ⚽</span></div>`
            ).join('');
        }
    }

    function escHtml(str) {
        return String(str)
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    refresh();
    setInterval(refresh, 2000);
</script>
</body>
</html>
"""
