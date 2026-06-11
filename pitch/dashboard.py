"""Dashboard module for The Pitch.

Serves the main control panel at / — a dark-themed, FIFA World Cup 2026
branded page with match controls, Tactical Coach AI, per-player role cards,
strategy library, leaderboard, and a live debug console.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    """Serve the main control panel dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Football Soccer – LLM Driven</title>
  <style>
    /* ── Reset & base ─────────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:       #0d0d0d;
      --surface:  #141414;
      --surface2: #1a1a1a;
      --border:   #2a2a2a;
      --cyan:     #00e5cc;
      --cyan-dim: #00b8a0;
      --green:    #22c55e;
      --purple:   #9333ea;
      --purple-dim:#7c3aed;
      --red:      #be123c;
      --red-dim:  #9f1239;
      --orange:   #f97316;
      --yellow:   #eab308;
      --text:     #e5e5e5;
      --text-dim: #737373;
      --text-muted:#404040;
      --radius:   6px;
    }
    html { font-size: 14px; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }

    /* ── Scrollbar ────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

    /* ── Header ───────────────────────────────────────────────────── */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 12px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .header-left { display: flex; flex-direction: column; gap: 2px; }
    .header-status { display: flex; align-items: center; gap: 8px; }
    .status-dot {
      width: 9px; height: 9px; border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 6px var(--green);
      flex-shrink: 0;
    }
    .header-title {
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--cyan);
      letter-spacing: -0.3px;
    }
    .header-sub {
      font-size: 0.72rem;
      color: var(--text-dim);
      letter-spacing: 1.5px;
      text-transform: uppercase;
    }
    .lang-select {
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 5px 10px;
      border-radius: var(--radius);
      font-size: 0.82rem;
      cursor: pointer;
      outline: none;
    }
    .lang-select:focus { border-color: var(--cyan-dim); }

    /* ── Layout ───────────────────────────────────────────────────── */
    .layout {
      display: grid;
      grid-template-columns: 340px 1fr;
      height: calc(100vh - 57px);
      overflow: hidden;
    }
    .sidebar {
      border-right: 1px solid var(--border);
      overflow-y: auto;
      padding: 14px 14px 40px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .main-panel {
      overflow-y: auto;
      padding: 14px 18px 40px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    /* ── Cards / Sections ─────────────────────────────────────────── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      cursor: pointer;
      user-select: none;
      border-bottom: 1px solid var(--border);
    }
    .card-header:hover { background: var(--surface2); }
    .card-title {
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .chevron {
      color: var(--text-dim);
      transition: transform 0.2s;
      font-size: 0.9rem;
    }
    .chevron.open { transform: rotate(180deg); }
    .card-body { padding: 12px 14px; }
    .card-body.hidden { display: none; }

    /* ── Buttons ──────────────────────────────────────────────────── */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: var(--radius);
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.6px;
      text-transform: uppercase;
      cursor: pointer;
      border: 1px solid transparent;
      transition: opacity 0.15s, background 0.15s;
      white-space: nowrap;
    }
    .btn:active { opacity: 0.8; }
    .btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .btn-dark    { background: #1f1f1f; border-color: #333; color: var(--text); }
    .btn-dark:hover:not(:disabled) { background: #282828; }
    .btn-red     { background: var(--red); border-color: var(--red-dim); color: #fff; }
    .btn-red:hover:not(:disabled) { background: var(--red-dim); }
    .btn-purple  { background: var(--purple); border-color: var(--purple-dim); color: #fff; }
    .btn-purple:hover:not(:disabled) { background: var(--purple-dim); }
    .btn-green   { background: #15803d; border-color: #166534; color: #fff; }
    .btn-green:hover:not(:disabled) { background: #166534; }
    .btn-full    { width: 100%; }
    .btn-row     { display: flex; gap: 8px; }
    .btn-row .btn { flex: 1; }

    /* ── Match Setup ──────────────────────────────────────────────── */
    .match-live-bar {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 10px 14px;
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
    }
    .score-team { font-size: 0.75rem; color: var(--text-dim); letter-spacing: 0.5px; }
    .score-team.red  { color: #f87171; }
    .score-team.blue { color: #60a5fa; text-align: right; }
    .score-val { font-size: 1.6rem; font-weight: 800; color: var(--text); text-align: center; }
    .match-status-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      padding: 3px 8px;
      border-radius: 20px;
      background: var(--surface2);
      border: 1px solid var(--border);
    }
    .match-status-pill.playing { border-color: var(--green); color: var(--green); }
    .match-status-pill.waiting { border-color: var(--yellow); color: var(--yellow); }
    .timer-bar { text-align: center; font-size: 0.72rem; color: var(--text-dim); margin-top: 4px; }

    /* ── Team Tabs ────────────────────────────────────────────────── */
    .tabs {
      display: flex;
      gap: 0;
      border-bottom: 1px solid var(--border);
      margin-bottom: 12px;
    }
    .tab-btn {
      padding: 8px 14px;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-dim);
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: color 0.15s;
    }
    .tab-btn:hover { color: var(--text); }
    .tab-btn.active { color: var(--green); border-bottom-color: var(--green); }
    .team-badge {
      font-size: 0.65rem;
      font-weight: 700;
      padding: 2px 5px;
      border-radius: 3px;
      text-transform: uppercase;
    }
    .badge-ch { background: #0e4a4a; color: var(--cyan); }
    .badge-de { background: #4a2900; color: var(--orange); }

    /* ── Coach AI Card ────────────────────────────────────────────── */
    .coach-card {
      background: var(--surface);
      border: 1px solid var(--purple);
      border-radius: var(--radius);
      padding: 14px;
      margin-bottom: 10px;
    }
    .coach-card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }
    .coach-card-title {
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: var(--purple);
    }
    .sparkle { font-size: 1rem; }
    .coach-desc {
      font-size: 0.75rem;
      color: var(--text-dim);
      margin-bottom: 10px;
      line-height: 1.4;
    }
    .coach-input {
      width: 100%;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      color: var(--text);
      padding: 8px 10px;
      font-size: 0.8rem;
      resize: none;
      height: 64px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
    }
    .coach-input:focus { border-color: var(--purple-dim); }
    .coach-footer { display: flex; justify-content: flex-end; margin-top: 8px; }

    /* ── Player Role Cards ────────────────────────────────────────── */
    .role-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      margin-bottom: 6px;
      overflow: hidden;
    }
    .role-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 9px 12px;
      cursor: pointer;
      user-select: none;
    }
    .role-card-header:hover { background: var(--surface2); }
    .role-left { display: flex; align-items: center; gap: 8px; }
    .role-title {
      font-size: 0.77rem;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }
    .status-badge {
      font-size: 0.62rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 20px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .status-active   { background: #052e16; color: var(--green); border: 1px solid #166534; }
    .status-inactive { background: #1c1c1c; color: var(--text-dim); border: 1px solid var(--border); }
    .role-card-body { padding: 10px 12px 12px; border-top: 1px solid var(--border); }

    /* ── Style Tags ───────────────────────────────────────────────── */
    .style-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 8px; }
    .style-tag {
      font-size: 0.7rem;
      padding: 3px 8px;
      border-radius: 20px;
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text-dim);
      cursor: pointer;
      transition: border-color 0.15s, color 0.15s, background 0.15s;
      user-select: none;
    }
    .style-tag:hover { border-color: #444; color: var(--text); }
    .style-tag.selected { border-color: var(--cyan-dim); color: var(--cyan); background: #0e2e2a; }

    /* ── Prompt Area ──────────────────────────────────────────────── */
    .prompt-area {
      width: 100%;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      color: var(--text);
      padding: 8px 10px;
      font-size: 0.78rem;
      resize: vertical;
      min-height: 60px;
      font-family: inherit;
      outline: none;
      line-height: 1.5;
      transition: border-color 0.2s;
    }
    .prompt-area:focus { border-color: var(--cyan-dim); }

    /* ── Collapsible extra sections ───────────────────────────────── */
    .section-count {
      font-size: 0.7rem;
      color: var(--text-muted);
      background: var(--surface2);
      padding: 1px 6px;
      border-radius: 10px;
      border: 1px solid var(--border);
    }

    /* ── Debug Console ────────────────────────────────────────────── */
    .debug-label {
      font-size: 0.72rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 6px;
    }
    .debug-console {
      background: #0a0a0a;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 10px 12px;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.73rem;
      color: #a3e635;
      min-height: 120px;
      max-height: 260px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }

    /* ── Live scoreboard strip ────────────────────────────────────── */
    .scoreboard-link {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.72rem;
      color: var(--text-dim);
      text-decoration: none;
      padding: 4px 8px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      transition: color 0.15s, border-color 0.15s;
    }
    .scoreboard-link:hover { color: var(--cyan); border-color: var(--cyan-dim); }

    /* ── Toast notification ───────────────────────────────────────── */
    #toast {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 10px 16px;
      font-size: 0.82rem;
      color: var(--text);
      box-shadow: 0 4px 16px rgba(0,0,0,0.5);
      opacity: 0;
      transform: translateY(8px);
      transition: opacity 0.25s, transform 0.25s;
      pointer-events: none;
      z-index: 9999;
      max-width: 280px;
    }
    #toast.show { opacity: 1; transform: translateY(0); }
    #toast.success { border-color: var(--green); }
    #toast.error   { border-color: var(--red); }

    /* ── Input / label ────────────────────────────────────────────── */
    label {
      font-size: 0.72rem;
      color: var(--text-dim);
      display: block;
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    input[type=text] {
      width: 100%;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      color: var(--text);
      padding: 7px 10px;
      font-size: 0.8rem;
      outline: none;
      transition: border-color 0.2s;
    }
    input[type=text]:focus { border-color: var(--cyan-dim); }

    /* ── Divider ──────────────────────────────────────────────────── */
    hr { border: none; border-top: 1px solid var(--border); margin: 8px 0; }

    /* ── Scrollable strategy list ─────────────────────────────────── */
    .strategy-item {
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
      font-size: 0.78rem;
      color: var(--text-dim);
    }
    .strategy-item:last-child { border-bottom: none; }
  </style>
</head>
<body>

<!-- ── Header ───────────────────────────────────────────────────────── -->
<header>
  <div class="header-left">
    <div class="header-status">
      <span class="status-dot" id="server-dot"></span>
      <span class="header-title">Football Soccer – LLM Driven</span>
    </div>
    <div class="header-sub">vs FIFA WORLD CUP 2026 &middot; USA &middot; CANADA &middot; MEXICO</div>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <a href="/scoreboard" class="scoreboard-link" target="_blank">&#128200; Scoreboard</a>
    <select class="lang-select" id="lang-select" onchange="setLanguage(this.value)">
      <option value="en">🌐 English</option>
      <option value="es">🌐 Español</option>
      <option value="fr">🌐 Français</option>
      <option value="pt">🌐 Português</option>
      <option value="de">🌐 Deutsch</option>
      <option value="ar">🌐 العربية</option>
      <option value="zh">🌐 中文</option>
      <option value="ja">🌐 日本語</option>
    </select>
  </div>
</header>

<!-- ── Main layout ───────────────────────────────────────────────────── -->
<div class="layout">

  <!-- ── Sidebar ──────────────────────────────────────────────────── -->
  <aside class="sidebar">

    <!-- Match Live Bar -->
    <div class="match-live-bar">
      <div>
        <div class="score-team red" data-i18n="team_red">RED</div>
      </div>
      <div style="text-align:center;">
        <div class="score-val" id="score-val">0 – 0</div>
        <div id="match-pill" class="match-status-pill waiting">
          <span id="pill-dot">⏳</span>
          <span id="pill-text" data-i18n="waiting">WAITING</span>
        </div>
      </div>
      <div style="text-align:right;">
        <div class="score-team blue" data-i18n="team_blue">BLUE</div>
      </div>
    </div>
    <div class="timer-bar">⏱ <span id="timer-val">90.0</span>s <span data-i18n="remaining">remaining</span></div>

    <!-- Match Setup -->
    <div class="card">
      <div class="card-header" onclick="toggleCard('match-setup')">
        <span class="card-title">🏆 <span data-i18n="match_setup">Match Setup</span></span>
        <span class="chevron open" id="chevron-match-setup">▼</span>
      </div>
      <div class="card-body" id="body-match-setup">
        <div class="btn-row" style="margin-bottom:8px;">
          <button class="btn btn-dark" id="btn-start" onclick="matchControl('start')">
            ▶ <span data-i18n="start_match">START MATCH</span>
          </button>
          <button class="btn btn-red" id="btn-end" onclick="matchControl('end')">
            🏁 <span data-i18n="end_match">END MATCH</span>
          </button>
        </div>
        <div class="btn-row">
          <button class="btn btn-dark" onclick="matchControl('reset-ball')">
            ⚽ <span data-i18n="reset_ball">RESET BALL</span>
          </button>
          <button class="btn btn-red" onclick="matchControl('reset-match')">
            ⏮ <span data-i18n="reset_match">RESET MATCH</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Strategy Library -->
    <div class="card">
      <div class="card-header" onclick="toggleCard('strategy-lib')">
        <span class="card-title">📚 <span data-i18n="strategy_library">Strategy Library</span>
          <span class="section-count" id="strategy-count">0</span>
        </span>
        <span class="chevron" id="chevron-strategy-lib">▼</span>
      </div>
      <div class="card-body hidden" id="body-strategy-lib">
        <div id="strategy-list">
          <div class="strategy-item" style="color:var(--text-muted);font-style:italic;" data-i18n="no_strategies">No saved strategies yet.</div>
        </div>
        <hr>
        <div style="margin-top:8px;">
          <label data-i18n="save_strategy_label">Save current prompts as strategy</label>
          <div style="display:flex;gap:6px;margin-top:4px;">
            <input type="text" id="strategy-name-input" placeholder="Strategy name…" style="flex:1;" />
            <button class="btn btn-dark" onclick="saveStrategy()" data-i18n="save">Save</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tournament Leaderboard -->
    <div class="card">
      <div class="card-header" onclick="toggleCard('leaderboard')">
        <span class="card-title">🏆 <span data-i18n="tournament_leaderboard">Tournament Leaderboard</span>
          <span class="section-count" id="lb-count">0</span>
        </span>
        <span class="chevron" id="chevron-leaderboard">▼</span>
      </div>
      <div class="card-body hidden" id="body-leaderboard">
        <div id="leaderboard-list">
          <div class="strategy-item" style="color:var(--text-muted);font-style:italic;" data-i18n="no_matches">No matches recorded.</div>
        </div>
      </div>
    </div>

    <!-- Live Synced Strategies -->
    <div class="card">
      <div class="card-header" onclick="toggleCard('live-sync')">
        <span class="card-title">📡 <span data-i18n="live_synced">Live Synced Strategies</span>
          <span class="section-count">0</span>
        </span>
        <span class="chevron" id="chevron-live-sync">▼</span>
      </div>
      <div class="card-body hidden" id="body-live-sync">
        <div class="strategy-item" style="color:var(--text-muted);font-style:italic;" data-i18n="no_synced">No synced strategies available.</div>
      </div>
    </div>

    <!-- Debug Console -->
    <div>
      <div class="debug-label" data-i18n="debug_console">Debug Console</div>
      <div class="debug-console" id="debug-console">{}</div>
    </div>

  </aside>

  <!-- ── Main Panel ────────────────────────────────────────────────── -->
  <main class="main-panel">

    <!-- Coach your team label -->
    <div>
      <div style="font-size:1rem;font-weight:700;margin-bottom:2px;" data-i18n="coach_team">Coach your team</div>
      <div style="font-size:0.75rem;color:var(--text-dim);" data-i18n="coach_sub">Four roles per side. Empty prompt = player inactive.</div>
    </div>

    <!-- Team Tabs -->
    <div class="tabs" id="team-tabs">
      <button class="tab-btn active" id="tab-red" onclick="switchTeam('Red')">
        <span class="team-badge badge-ch">RED</span>
        <span id="tab-red-name" data-i18n="team_red_label">Red Team</span>
      </button>
      <button class="tab-btn" id="tab-blue" onclick="switchTeam('Blue')">
        <span class="team-badge badge-de">BLUE</span>
        <span id="tab-blue-name" data-i18n="team_blue_label">Blue Team</span>
      </button>
    </div>

    <!-- Tactical Coach AI -->
    <div class="coach-card" id="coach-card">
      <div class="coach-card-header">
        <span class="sparkle">✨</span>
        <span class="coach-card-title" data-i18n="tactical_coach_ai">TACTICAL COACH AI</span>
      </div>
      <div class="coach-desc" data-i18n="coach_ai_desc">Tell the coach what you want — it writes a full game plan for your team.</div>
      <textarea class="coach-input" id="coach-prompt-input" data-i18n-placeholder="coach_placeholder"
        placeholder="e.g. tiki-taka, park the bus, gegenpressing, total football..."></textarea>
      <div class="coach-footer">
        <button class="btn btn-purple" onclick="generateCoachPlan()">
          ✦ <span data-i18n="generate">GENERATE</span>
        </button>
      </div>
    </div>

    <!-- Player Role Cards -->
    <div id="role-cards">
      <!-- Dynamically rendered -->
    </div>

  </main>
</div>

<!-- Toast -->
<div id="toast"></div>

<script>
/* ═══════════════════════════════════════════════════════════════════
   STATE
═══════════════════════════════════════════════════════════════════ */
const POSITIONS = ['Striker', 'Midfielder', 'Defender', 'Goalkeeper'];
const DEFAULT_PROMPTS = {
  Striker:    'First to every ball. No hesitation, no waiting. The moment you get a touch, hit the target — hard.',
  Midfielder: 'Control the tempo. Win the ball back fast and distribute with precision.',
  Defender:   'Stay between the ball and goal. Clear danger, support the keeper.',
  Goalkeeper: 'Command your area. Catch everything in range, distribute quickly to launch attacks.',
};
const STYLE_TAGS = {
  Striker:    ['🔥 Aggressive', '🎯 Sniper', '↔ Counter', '🤝 Team Player'],
  Midfielder: ['⚡ Box-to-Box', '🎭 Creative', '🛡 Defensive Mid', '↔ Counter'],
  Defender:   ['🧱 Rock Solid', '📐 Tactical', '🚀 Sweeper', '↔ Counter'],
  Goalkeeper: ['🧤 Shot Stopper', '🦵 Sweeper-Keeper', '📢 Commander', '🎯 Distributor'],
};

let currentTeam = 'Red';
let promptData = { Red: {}, Blue: {} };
let selectedTags = { Red: {}, Blue: {} };
let leaderboard = JSON.parse(localStorage.getItem('lb') || '[]');
let strategies = JSON.parse(localStorage.getItem('strats') || '[]');
let lastState = {};

// Init defaults
POSITIONS.forEach(p => {
  ['Red','Blue'].forEach(t => {
    promptData[t][p] = DEFAULT_PROMPTS[p];
    selectedTags[t][p] = [];
  });
});

/* ═══════════════════════════════════════════════════════════════════
   I18N
═══════════════════════════════════════════════════════════════════ */
const TRANSLATIONS = {
  en: {},
  es: {
    'Football Soccer – LLM Driven': 'Fútbol – Impulsado por LLM',
    'match_setup': 'Configuración del Partido',
    'start_match': 'INICIAR PARTIDO',
    'end_match': 'TERMINAR PARTIDO',
    'reset_ball': 'RESETEAR BALÓN',
    'reset_match': 'RESETEAR PARTIDO',
    'coach_team': 'Entrena a tu equipo',
    'coach_sub': 'Cuatro roles por lado. Prompt vacío = jugador inactivo.',
    'tactical_coach_ai': 'ENTRENADOR TÁCTICO IA',
    'coach_ai_desc': 'Dile al entrenador qué quieres — genera un plan de juego completo.',
    'coach_placeholder': 'ej. tiki-taka, autobús, gegenpressing…',
    'generate': 'GENERAR',
    'waiting': 'ESPERANDO',
    'playing': 'JUGANDO',
    'remaining': 'restantes',
    'team_red': 'ROJO',
    'team_blue': 'AZUL',
    'team_red_label': 'Equipo Rojo',
    'team_blue_label': 'Equipo Azul',
    'strategy_library': 'Biblioteca de Estrategias',
    'tournament_leaderboard': 'Tabla de Clasificación',
    'live_synced': 'Estrategias Sincronizadas',
    'debug_console': 'Consola de Depuración',
    'save': 'Guardar',
    'no_strategies': 'Sin estrategias guardadas.',
    'no_matches': 'Sin partidos registrados.',
    'no_synced': 'Sin estrategias sincronizadas.',
    'save_strategy_label': 'Guardar prompts actuales como estrategia',
  },
  fr: {
    'match_setup': 'Configuration du Match',
    'start_match': 'DÉMARRER',
    'end_match': 'TERMINER',
    'reset_ball': 'RESET BALLE',
    'reset_match': 'RESET MATCH',
    'coach_team': 'Entraîne ton équipe',
    'coach_sub': 'Quatre rôles par équipe. Prompt vide = joueur inactif.',
    'tactical_coach_ai': 'ENTRAÎNEUR TACTIQUE IA',
    'generate': 'GÉNÉRER',
    'waiting': 'EN ATTENTE',
    'playing': 'EN JEU',
    'remaining': 'restantes',
    'team_red_label': 'Équipe Rouge',
    'team_blue_label': 'Équipe Bleue',
  },
};

let currentLang = 'en';
function setLanguage(lang) {
  currentLang = lang;
  const t = TRANSLATIONS[lang] || {};
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.textContent = t[key];
    else if (TRANSLATIONS.en[key]) el.textContent = TRANSLATIONS.en[key];
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (t[key]) el.placeholder = t[key];
  });
}

/* ═══════════════════════════════════════════════════════════════════
   TOGGLE CARDS
═══════════════════════════════════════════════════════════════════ */
function toggleCard(id) {
  const body = document.getElementById('body-' + id);
  const ch   = document.getElementById('chevron-' + id);
  if (!body) return;
  body.classList.toggle('hidden');
  ch && ch.classList.toggle('open');
}

/* ═══════════════════════════════════════════════════════════════════
   TEAM TABS
═══════════════════════════════════════════════════════════════════ */
function switchTeam(team) {
  // Save current prompts before switching
  saveCurrentPrompts();

  currentTeam = team;
  document.getElementById('tab-red').classList.toggle('active', team === 'Red');
  document.getElementById('tab-blue').classList.toggle('active', team === 'Blue');
  renderRoleCards();
}

function saveCurrentPrompts() {
  POSITIONS.forEach(pos => {
    const ta = document.getElementById('prompt-' + pos);
    if (ta) promptData[currentTeam][pos] = ta.value;
  });
}

/* ═══════════════════════════════════════════════════════════════════
   ROLE CARDS
═══════════════════════════════════════════════════════════════════ */
function renderRoleCards() {
  const container = document.getElementById('role-cards');
  const team = currentTeam;
  const badgeClass = team === 'Red' ? 'badge-ch' : 'badge-de';
  const badgeText  = team === 'Red' ? 'RED' : 'BLUE';

  container.innerHTML = POSITIONS.map((pos, i) => {
    const prompt = promptData[team][pos] || '';
    const active = prompt.trim().length > 0;
    const tags   = STYLE_TAGS[pos] || [];
    const selTags = selectedTags[team][pos] || [];
    const isOpen  = i === 0; // first card open by default

    const tagsHtml = tags.map(tag => {
      const isSel = selTags.includes(tag);
      return `<span class="style-tag${isSel ? ' selected' : ''}" onclick="toggleTag('${pos}','${escHtml(tag)}')">${escHtml(tag)}</span>`;
    }).join('');

    return `
    <div class="role-card" id="role-card-${pos}">
      <div class="role-card-header" onclick="toggleRoleCard('${pos}')">
        <div class="role-left">
          <span class="team-badge ${badgeClass}">${badgeText}</span>
          <span class="role-title">${pos}</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="status-badge ${active ? 'status-active' : 'status-inactive'}">
            ${active ? '🟢 ACTIVE' : '⚪ INACTIVE'}
          </span>
          <span class="chevron ${isOpen ? 'open' : ''}" id="chevron-role-${pos}">▼</span>
        </div>
      </div>
      <div class="role-card-body${isOpen ? '' : ' hidden'}" id="body-role-${pos}">
        <div class="style-tags" id="tags-${pos}">${tagsHtml}</div>
        <textarea class="prompt-area" id="prompt-${pos}" rows="3"
          onchange="onPromptChange('${pos}')"
          oninput="onPromptChange('${pos}')"
          placeholder="Tactical instructions for ${pos}…">${escHtml(prompt)}</textarea>
        <div style="display:flex;justify-content:flex-end;margin-top:6px;">
          <button class="btn btn-dark" style="font-size:0.7rem;padding:5px 10px;" onclick="clearPrompt('${pos}')">✕ Clear</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

function toggleRoleCard(pos) {
  const body = document.getElementById('body-role-' + pos);
  const ch   = document.getElementById('chevron-role-' + pos);
  body.classList.toggle('hidden');
  ch && ch.classList.toggle('open');
}

function toggleTag(pos, tag) {
  const arr = selectedTags[currentTeam][pos] || [];
  const idx = arr.indexOf(tag);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(tag);
  selectedTags[currentTeam][pos] = arr;
  // Re-render just the tag strip
  const strip = document.getElementById('tags-' + pos);
  if (!strip) return;
  const tags = STYLE_TAGS[pos] || [];
  strip.innerHTML = tags.map(t => {
    const isSel = arr.includes(t);
    return `<span class="style-tag${isSel ? ' selected' : ''}" onclick="toggleTag('${pos}','${escHtml(t)}')">${escHtml(t)}</span>`;
  }).join('');
}

function onPromptChange(pos) {
  promptData[currentTeam][pos] = document.getElementById('prompt-' + pos).value;
  // Update status badge
  const badge = document.querySelector(`#role-card-${pos} .status-badge`);
  if (badge) {
    const active = promptData[currentTeam][pos].trim().length > 0;
    badge.className = `status-badge ${active ? 'status-active' : 'status-inactive'}`;
    badge.textContent = active ? '🟢 ACTIVE' : '⚪ INACTIVE';
  }
}

function clearPrompt(pos) {
  const ta = document.getElementById('prompt-' + pos);
  if (ta) { ta.value = ''; promptData[currentTeam][pos] = ''; onPromptChange(pos); }
}

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

/* ═══════════════════════════════════════════════════════════════════
   MATCH CONTROLS
═══════════════════════════════════════════════════════════════════ */
async function matchControl(action) {
  try {
    const res = await fetch(`/api/match/${action}`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast('✓ ' + (data.message || action + ' done'), 'success');
      refreshState();
    } else {
      showToast('✗ ' + (data.error || 'Failed'), 'error');
    }
  } catch(e) {
    showToast('✗ Connection error', 'error');
  }
}

/* ═══════════════════════════════════════════════════════════════════
   TACTICAL COACH AI (local generation)
═══════════════════════════════════════════════════════════════════ */
const COACH_TEMPLATES = {
  'tiki-taka':    { Striker: 'Make sharp runs, receive quick passes, one-touch play. Stay connected to midfield.', Midfielder: 'Short passes, triangles, keep possession. Press immediately on loss.', Defender: 'Build from the back with short passes. Cover space, do not lunge.', Goalkeeper: 'Distribute short to defenders. Start build-up play calmly.' },
  'park the bus': { Striker: 'Hold the ball up, protect leads, do not over-commit forward.', Midfielder: 'Sit deep, block passing lanes, hard tackles allowed.', Defender: 'Stay compact, never step out, clear danger decisively.', Goalkeeper: 'Command penalty area, communicate loudly, clear long.' },
  'gegenpressing': { Striker: 'Press the ball carrier instantly on loss. Force errors in their half.', Midfielder: 'Sprint press, win second balls, transition quickly.', Defender: 'Push high, aggressive line, cover behind with pace.', Goalkeeper: 'Sweeper-keeper, rush off line, start counter-attacks.' },
  'total football': { Striker: 'Drop into midfield to create overloads. Interchangeable movement.', Midfielder: 'Roam freely, cover all zones, interchange with any position.', Defender: 'Join attacks, overlap, be comfortable with the ball.', Goalkeeper: 'Distribute precisely to feet to start positional play.' },
  'counter':       { Striker: 'Burst forward the moment possession is won. Run in behind.', Midfielder: 'Win ball fast, release striker immediately with direct pass.', Defender: 'Stay deep, absorb pressure, trigger quick vertical ball.', Goalkeeper: 'Launch fast distribution on saves. Long ball to striker.' },
  'high press':    { Striker: 'Press goalkeeper and defenders on every goal kick.', Midfielder: 'Chase every ball, double-press, force long balls.', Defender: 'High line, close gaps, confident dealing with balls in behind.', Goalkeeper: 'Sweeper-keeper, dominates 18-yard box, quick feet.' },
};

function generateCoachPlan() {
  const rawPrompt = document.getElementById('coach-prompt-input').value.trim().toLowerCase();
  let matched = null;
  for (const key of Object.keys(COACH_TEMPLATES)) {
    if (rawPrompt.includes(key)) { matched = key; break; }
  }

  const plan = matched
    ? COACH_TEMPLATES[matched]
    : {
        Striker:    rawPrompt ? `${rawPrompt.slice(0,120)} — get on the ball and shoot.` : DEFAULT_PROMPTS.Striker,
        Midfielder: rawPrompt ? `${rawPrompt.slice(0,120)} — control the midfield.`      : DEFAULT_PROMPTS.Midfielder,
        Defender:   rawPrompt ? `${rawPrompt.slice(0,120)} — defensive discipline.`      : DEFAULT_PROMPTS.Defender,
        Goalkeeper: rawPrompt ? `${rawPrompt.slice(0,120)} — keep the clean sheet.`      : DEFAULT_PROMPTS.Goalkeeper,
      };

  POSITIONS.forEach(pos => { promptData[currentTeam][pos] = plan[pos]; });
  renderRoleCards();
  showToast('✓ Game plan generated for ' + currentTeam, 'success');
}

/* ═══════════════════════════════════════════════════════════════════
   STRATEGY LIBRARY
═══════════════════════════════════════════════════════════════════ */
function saveStrategy() {
  const nameEl = document.getElementById('strategy-name-input');
  const name = nameEl ? nameEl.value.trim() : '';
  if (!name) { showToast('Enter a strategy name', 'error'); return; }
  saveCurrentPrompts();
  const strat = {
    name,
    team: currentTeam,
    prompts: JSON.parse(JSON.stringify(promptData[currentTeam])),
    tags: JSON.parse(JSON.stringify(selectedTags[currentTeam])),
    saved: new Date().toISOString(),
  };
  strategies.push(strat);
  localStorage.setItem('strats', JSON.stringify(strategies));
  if (nameEl) nameEl.value = '';
  renderStrategyList();
  showToast('✓ Strategy saved: ' + name, 'success');
}

function loadStrategy(idx) {
  const strat = strategies[idx];
  if (!strat) return;
  currentTeam = strat.team;
  promptData[strat.team] = JSON.parse(JSON.stringify(strat.prompts));
  selectedTags[strat.team] = JSON.parse(JSON.stringify(strat.tags));
  document.getElementById('tab-red').classList.toggle('active', strat.team === 'Red');
  document.getElementById('tab-blue').classList.toggle('active', strat.team === 'Blue');
  renderRoleCards();
  showToast('✓ Loaded: ' + strat.name, 'success');
}

function deleteStrategy(idx) {
  strategies.splice(idx, 1);
  localStorage.setItem('strats', JSON.stringify(strategies));
  renderStrategyList();
}

function renderStrategyList() {
  const el = document.getElementById('strategy-list');
  const count = document.getElementById('strategy-count');
  if (count) count.textContent = strategies.length;
  if (!el) return;
  if (strategies.length === 0) {
    el.innerHTML = '<div class="strategy-item" style="color:var(--text-muted);font-style:italic;">No saved strategies yet.</div>';
    return;
  }
  el.innerHTML = strategies.map((s, i) => `
    <div class="strategy-item" style="display:flex;align-items:center;justify-content:space-between;gap:6px;">
      <div>
        <span style="color:var(--text);font-weight:600;">${escHtml(s.name)}</span>
        <span style="color:var(--text-dim);font-size:0.7rem;margin-left:6px;">${s.team}</span>
      </div>
      <div style="display:flex;gap:4px;">
        <button class="btn btn-dark" style="padding:3px 8px;font-size:0.68rem;" onclick="loadStrategy(${i})">Load</button>
        <button class="btn btn-red"  style="padding:3px 8px;font-size:0.68rem;" onclick="deleteStrategy(${i})">✕</button>
      </div>
    </div>`
  ).join('');
}

/* ═══════════════════════════════════════════════════════════════════
   LEADERBOARD (persisted in localStorage)
═══════════════════════════════════════════════════════════════════ */
function addToLeaderboard(score, matchState) {
  if (matchState !== 'Waiting') return; // only record completed matches
  const red = score.Red || 0;
  const blue = score.Blue || 0;
  if (red === 0 && blue === 0) return;
  // Check if this score was already recorded (avoid duplicates on state polls)
  const last = leaderboard[leaderboard.length - 1];
  if (last && last.red === red && last.blue === blue) return;
  leaderboard.push({ red, blue, date: new Date().toLocaleDateString() });
  if (leaderboard.length > 20) leaderboard.shift();
  localStorage.setItem('lb', JSON.stringify(leaderboard));
  renderLeaderboard();
}

function renderLeaderboard() {
  const el = document.getElementById('leaderboard-list');
  const count = document.getElementById('lb-count');
  if (count) count.textContent = leaderboard.length;
  if (!el) return;
  if (leaderboard.length === 0) {
    el.innerHTML = '<div class="strategy-item" style="color:var(--text-muted);font-style:italic;">No matches recorded.</div>';
    return;
  }
  el.innerHTML = [...leaderboard].reverse().map((m, i) => `
    <div class="strategy-item" style="display:flex;justify-content:space-between;">
      <span style="color:var(--text-dim);">#${leaderboard.length - i}</span>
      <span>
        <span style="color:#f87171;">${m.red}</span>
        &ndash;
        <span style="color:#60a5fa;">${m.blue}</span>
      </span>
      <span style="color:var(--text-muted);font-size:0.7rem;">${m.date}</span>
    </div>`
  ).join('');
}

/* ═══════════════════════════════════════════════════════════════════
   LIVE STATE POLLING
═══════════════════════════════════════════════════════════════════ */
async function refreshState() {
  try {
    const res = await fetch('/api/state');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    lastState = data;
    updateHUD(data);
    updateDebugConsole(data);
    document.getElementById('server-dot').style.background = 'var(--green)';
    document.getElementById('server-dot').style.boxShadow  = '0 0 6px var(--green)';
    // Record leaderboard entry when match transitions to Waiting
    addToLeaderboard(data.score || {}, data.match_state);
  } catch(e) {
    document.getElementById('server-dot').style.background = '#ef4444';
    document.getElementById('server-dot').style.boxShadow  = '0 0 6px #ef4444';
  }
}

function updateHUD(data) {
  const red  = (data.score || {}).Red  || 0;
  const blue = (data.score || {}).Blue || 0;
  document.getElementById('score-val').textContent  = red + ' – ' + blue;
  document.getElementById('timer-val').textContent  = parseFloat(data.time_left || 0).toFixed(1);
  const pill   = document.getElementById('match-pill');
  const dot    = document.getElementById('pill-dot');
  const txt    = document.getElementById('pill-text');
  const playing = data.match_state === 'Playing';
  pill.className = 'match-status-pill ' + (playing ? 'playing' : 'waiting');
  dot.textContent = playing ? '🟢' : '⏳';
  txt.textContent = playing ? 'PLAYING' : 'WAITING';
}

function updateDebugConsole(data) {
  const el = document.getElementById('debug-console');
  if (el) el.textContent = JSON.stringify(data, null, 2);
}

/* ═══════════════════════════════════════════════════════════════════
   TOAST
═══════════════════════════════════════════════════════════════════ */
let toastTimer;
function showToast(msg, type='success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'show ' + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.className = ''; }, 2800);
}

/* ═══════════════════════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════════════════════ */
renderRoleCards();
renderStrategyList();
renderLeaderboard();
refreshState();
setInterval(refreshState, 2000);
</script>
</body>
</html>
"""
