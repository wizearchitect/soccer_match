"""Dashboard module for The Pitch.

Serves the unified control panel + live pitch at /.
Layout: sidebar (controls) | pitch canvas + coach panel stacked.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    """Serve the unified dashboard with embedded live pitch."""
    return HTMLResponse(content=DASHBOARD_HTML)


@router.get("/pitch", response_class=HTMLResponse)
async def pitch_fullscreen() -> HTMLResponse:
    """Full-screen pitch view (standalone)."""
    return HTMLResponse(content=DASHBOARD_HTML)


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Football Soccer – LLM Driven</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:        #0d0d0d;
      --surface:   #141414;
      --surface2:  #1a1a1a;
      --border:    #2a2a2a;
      --cyan:      #00e5cc;
      --cyan-dim:  #00b8a0;
      --green:     #22c55e;
      --purple:    #9333ea;
      --purple-dim:#7c3aed;
      --red-clr:   #be123c;
      --red-dim:   #9f1239;
      --orange:    #f97316;
      --yellow:    #eab308;
      --text:      #e5e5e5;
      --text-dim:  #737373;
      --text-muted:#404040;
      --radius:    6px;
    }
    html, body { height: 100%; font-size: 16px; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Segoe UI', system-ui, sans-serif;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

    /* ══════════════════════════════════════════════════════════════
       HEADER
    ══════════════════════════════════════════════════════════════ */
    header {
      flex-shrink: 0;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 8px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .hdr-left { display: flex; flex-direction: column; gap: 1px; }
    .hdr-status { display: flex; align-items: center; gap: 7px; }
    .status-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: var(--green); box-shadow: 0 0 6px var(--green);
    }
    .hdr-title  { font-size: 1.1rem; font-weight: 700; color: var(--cyan); }
    .hdr-sub    { font-size: 0.62rem; color: var(--text-dim); letter-spacing: 1.2px; text-transform: uppercase; }
    .hdr-right  { display: flex; align-items: center; gap: 8px; }
    .hdr-link {
      font-size: 0.7rem; color: var(--text-dim); text-decoration: none;
      padding: 3px 8px; border: 1px solid var(--border); border-radius: var(--radius);
      transition: color .15s, border-color .15s;
    }
    .hdr-link:hover { color: var(--cyan); border-color: var(--cyan-dim); }
    .lang-sel {
      background: var(--surface2); border: 1px solid var(--border);
      color: var(--text); padding: 4px 8px; border-radius: var(--radius);
      font-size: 0.75rem; cursor: pointer; outline: none;
    }

    /* ══════════════════════════════════════════════════════════════
       BODY LAYOUT  —  sidebar | main
    ══════════════════════════════════════════════════════════════ */
    .layout {
      flex: 1;
      display: grid;
      grid-template-columns: 294px 416px 1fr;
      overflow: hidden;
    }

    /* ── Sidebar ── */
    .sidebar {
      border-right: 1px solid var(--border);
      overflow-y: auto;
      padding: 10px 10px 30px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    /* ── Right coach panel ── */
    .coach-panel {
      border-left: 1px solid var(--border);
      border-right: 1px solid var(--border);
      overflow-y: auto;
      padding: 10px 10px 30px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    /* ── Main panel ── */
    .main {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* ══════════════════════════════════════════════════════════════
       SCORE BAR  (inside main, above pitch)
    ══════════════════════════════════════════════════════════════ */
    .score-bar {
      flex-shrink: 0;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 6px 16px;
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 8px;
    }
    .sb-team      { font-size: 0.72rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
    .sb-team.red  { color: #f87171; }
    .sb-team.blue { color: #60a5fa; text-align: right; }
    .sb-centre    { display: flex; flex-direction: column; align-items: center; gap: 3px; }
    .sb-score     { font-size: 1.5rem; font-weight: 900; letter-spacing: -1px; }
    .sb-pill {
      font-size: 0.6rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
      padding: 2px 7px; border-radius: 20px; border: 1px solid var(--border);
    }
    .sb-pill.playing { border-color: var(--green); color: var(--green); }
    .sb-pill.waiting { border-color: var(--yellow); color: var(--yellow); }
    .sb-timer { font-size: 0.65rem; color: var(--text-dim); }

    /* ══════════════════════════════════════════════════════════════
       PITCH CANVAS
    ══════════════════════════════════════════════════════════════ */
    .pitch-wrap {
      flex: 1;
      min-height: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 8px;
      background: #0a0a0a;
    }
    canvas {
      display: block;
      max-width: 728px;
      width: 100%;
      height: auto;
      border: 2px solid #2a2a2a;
      border-radius: 5px;
    }

    /* ══════════════════════════════════════════════════════════════
       COACH STRIP  (below pitch)
    ══════════════════════════════════════════════════════════════ */
    .coach-strip {
      flex-shrink: 0;
      background: var(--surface);
      border-top: 1px solid var(--purple);
      padding: 8px 12px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .coach-strip-label {
      font-size: 0.65rem; font-weight: 700; letter-spacing: 1px;
      text-transform: uppercase; color: var(--purple); white-space: nowrap;
    }
    .coach-strip input {
      flex: 1;
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: var(--radius); color: var(--text);
      padding: 5px 9px; font-size: 0.78rem; outline: none;
      transition: border-color .2s;
    }
    .coach-strip input:focus { border-color: var(--purple-dim); }
    .btn-gen {
      background: var(--purple); border: 1px solid var(--purple-dim);
      color: #fff; padding: 5px 12px; border-radius: var(--radius);
      font-size: 0.72rem; font-weight: 700; letter-spacing: .5px;
      text-transform: uppercase; cursor: pointer; white-space: nowrap;
      transition: opacity .15s;
    }
    .btn-gen:active { opacity: .75; }

    /* ══════════════════════════════════════════════════════════════
       SHARED COMPONENTS
    ══════════════════════════════════════════════════════════════ */
    /* Card */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
    }
    .card-hdr {
      display: flex; align-items: center; justify-content: space-between;
      padding: 8px 11px; cursor: pointer; user-select: none;
      border-bottom: 1px solid var(--border);
    }
    .card-hdr:hover { background: var(--surface2); }
    .card-title {
      font-size: 0.72rem; font-weight: 600; letter-spacing: .5px;
      text-transform: uppercase; display: flex; align-items: center; gap: 5px;
    }
    .chevron { color: var(--text-dim); transition: transform .2s; font-size: .8rem; }
    .chevron.open { transform: rotate(180deg); }
    .card-body { padding: 10px 11px; }
    .card-body.hidden { display: none; }

    /* Buttons */
    .btn {
      display: inline-flex; align-items: center; justify-content: center;
      gap: 5px; padding: 6px 11px; border-radius: var(--radius);
      font-size: 0.72rem; font-weight: 600; letter-spacing: .5px;
      text-transform: uppercase; cursor: pointer; border: 1px solid transparent;
      transition: opacity .15s, background .15s; white-space: nowrap;
    }
    .btn:active { opacity: .8; }
    .btn-dark  { background: #1f1f1f; border-color: #333; color: var(--text); }
    .btn-dark:hover  { background: #282828; }
    .btn-red   { background: var(--red-clr); border-color: var(--red-dim); color: #fff; }
    .btn-red:hover   { background: var(--red-dim); }
    .btn-row   { display: flex; gap: 6px; }
    .btn-row .btn { flex: 1; }

    /* Score live bar in sidebar */
    .live-bar {
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 8px 10px;
      display: grid; grid-template-columns: 1fr auto 1fr;
      align-items: center; gap: 6px;
    }
    .lb-team       { font-size: 0.68rem; font-weight: 700; color: var(--text-dim); }
    .lb-team.red   { color: #f87171; }
    .lb-team.blue  { color: #60a5fa; text-align: right; }
    .lb-score      { font-size: 1.3rem; font-weight: 900; text-align: center; }
    .lb-pill       { text-align: center; font-size: 0.6rem; color: var(--text-dim); }

    /* Role cards */
    .role-card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); margin-bottom: 5px; overflow: hidden;
    }
    .role-hdr {
      display: flex; align-items: center; justify-content: space-between;
      padding: 7px 10px; cursor: pointer; user-select: none;
    }
    .role-hdr:hover { background: var(--surface2); }
    .role-left { display: flex; align-items: center; gap: 6px; }
    .role-title { font-size: 0.7rem; font-weight: 700; letter-spacing: .8px; text-transform: uppercase; }
    .badge { font-size: 0.58rem; font-weight: 700; padding: 1px 4px; border-radius: 3px; }
    .badge-r { background: #3a0a0a; color: #f87171; }
    .badge-b { background: #0a1a3a; color: #60a5fa; }
    .status-badge {
      font-size: 0.58rem; font-weight: 700; padding: 2px 6px;
      border-radius: 20px; letter-spacing: .5px; text-transform: uppercase;
    }
    .s-active   { background: #052e16; color: var(--green); border: 1px solid #166534; }
    .s-inactive { background: #1c1c1c; color: var(--text-dim); border: 1px solid var(--border); }
    .role-body  { padding: 8px 10px 10px; border-top: 1px solid var(--border); }
    .style-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px; }
    .style-tag {
      font-size: 0.65rem; padding: 2px 6px; border-radius: 20px;
      background: var(--surface2); border: 1px solid var(--border);
      color: var(--text-dim); cursor: pointer; user-select: none;
      transition: border-color .15s, color .15s;
    }
    .style-tag.sel { border-color: var(--cyan-dim); color: var(--cyan); background: #0e2e2a; }
    .prompt-area {
      width: 100%; background: var(--surface2); border: 1px solid var(--border);
      border-radius: var(--radius); color: var(--text); padding: 6px 8px;
      font-size: 0.72rem; resize: vertical; min-height: 52px;
      font-family: inherit; outline: none; line-height: 1.45;
      transition: border-color .2s;
    }
    .prompt-area:focus { border-color: var(--cyan-dim); }

    /* Misc */
    .section-count {
      font-size: 0.62rem; color: var(--text-muted);
      background: var(--surface2); padding: 1px 5px;
      border-radius: 10px; border: 1px solid var(--border);
    }
    .debug-con {
      background: #0a0a0a; border: 1px solid var(--border); border-radius: var(--radius);
      padding: 8px 10px; font-family: monospace; font-size: 0.68rem;
      color: #a3e635; min-height: 80px; max-height: 180px;
      overflow-y: auto; white-space: pre-wrap; word-break: break-all;
    }
    .strategy-item {
      padding: 6px 0; border-bottom: 1px solid var(--border);
      font-size: 0.72rem; color: var(--text-dim);
    }
    .strategy-item:last-child { border-bottom: none; }
    label { font-size: 0.65rem; color: var(--text-dim); display: block; margin-bottom: 3px;
            text-transform: uppercase; letter-spacing: .5px; }
    input[type=text] {
      width: 100%; background: var(--surface2); border: 1px solid var(--border);
      border-radius: var(--radius); color: var(--text); padding: 5px 8px;
      font-size: 0.75rem; outline: none; transition: border-color .2s;
    }
    input[type=text]:focus { border-color: var(--cyan-dim); }
    hr { border: none; border-top: 1px solid var(--border); margin: 6px 0; }

    /* Toast */
    #toast {
      position: fixed; bottom: 16px; right: 16px;
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 8px 14px;
      font-size: 0.78rem; color: var(--text);
      box-shadow: 0 4px 16px rgba(0,0,0,.5);
      opacity: 0; transform: translateY(6px);
      transition: opacity .25s, transform .25s;
      pointer-events: none; z-index: 9999;
    }
    #toast.show { opacity: 1; transform: translateY(0); }
    #toast.ok  { border-color: var(--green); }
    #toast.err { border-color: var(--red-clr); }

    /* Tabs */
    .tabs { display: flex; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
    .tab-btn {
      padding: 6px 11px; background: none; border: none;
      border-bottom: 2px solid transparent; color: var(--text-dim);
      font-size: 0.75rem; font-weight: 600; cursor: pointer;
      display: flex; align-items: center; gap: 5px; transition: color .15s;
    }
    .tab-btn:hover { color: var(--text); }
    .tab-btn.active { color: var(--green); border-bottom-color: var(--green); }
  </style>
</head>
<body>

<!-- ══════════════════ HEADER ══════════════════ -->
<header>
  <div class="hdr-left">
    <div class="hdr-status">
      <span class="status-dot" id="srv-dot"></span>
      <span class="hdr-title">Football Soccer – LLM Driven</span>
    </div>
    <div class="hdr-sub">vs FIFA WORLD CUP 2026 · USA · CANADA · MEXICO</div>
  </div>
  <div class="hdr-right">
    <a class="hdr-link" href="/scoreboard" target="_blank">📊 Scoreboard</a>
    <select class="lang-sel" onchange="setLang(this.value)">
      <option value="en">🌐 English</option>
      <option value="es">🌐 Español</option>
      <option value="fr">🌐 Français</option>
      <option value="pt">🌐 Português</option>
      <option value="ar">🌐 العربية</option>
      <option value="zh">🌐 中文</option>
    </select>
  </div>
</header>

<!-- ══════════════════ LAYOUT ══════════════════ -->
<div class="layout">

  <!-- ════════ SIDEBAR ════════ -->
  <aside class="sidebar">

    <!-- Live score mini-bar -->
    <div class="live-bar">
      <div class="lb-team red">RED</div>
      <div>
        <div class="lb-score" id="sb-score">0 – 0</div>
        <div class="lb-pill" id="sb-pill">⏳ WAITING</div>
      </div>
      <div class="lb-team blue">BLUE</div>
    </div>
    <div style="text-align:center;font-size:0.62rem;color:var(--text-dim);">
      ⏱ <span id="sb-timer">90.0</span>s remaining
    </div>

    <!-- Match Setup -->
    <div class="card">
      <div class="card-hdr" onclick="toggleCard('match')">
        <span class="card-title">🏆 Match Setup</span>
        <span class="chevron open" id="ch-match">▼</span>
      </div>
      <div class="card-body" id="bd-match">
        <div class="btn-row" style="margin-bottom:6px;">
          <button class="btn btn-dark" onclick="ctrl('start')">▶ Start</button>
          <button class="btn btn-red"  onclick="ctrl('end')">🏁 End</button>
        </div>
        <div class="btn-row">
          <button class="btn btn-dark" onclick="ctrl('reset-ball')">⚽ Reset Ball</button>
          <button class="btn btn-red"  onclick="ctrl('reset-match')">⏮ Reset Match</button>
        </div>
      </div>
    </div>

    <!-- Strategy Library -->
    <div class="card">
      <div class="card-hdr" onclick="toggleCard('strat')">
        <span class="card-title">📚 Strategy Library <span class="section-count" id="strat-count">0</span></span>
        <span class="chevron" id="ch-strat">▼</span>
      </div>
      <div class="card-body hidden" id="bd-strat">
        <div id="strat-list"><div class="strategy-item" style="color:var(--text-muted);font-style:italic;">No saved strategies.</div></div>
        <hr>
        <label>Save current as strategy</label>
        <div style="display:flex;gap:5px;margin-top:3px;">
          <input type="text" id="strat-name" placeholder="Name…" style="flex:1;"/>
          <button class="btn btn-dark" onclick="saveStrat()" style="padding:5px 9px;">Save</button>
        </div>
      </div>
    </div>

    <!-- Debug Console -->
    <div>
      <div style="font-size:0.62rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px;">Debug Console</div>
      <div class="debug-con" id="debug-con">{}</div>
    </div>

  </aside>

  <!-- ════════ COACH PANEL (centre column) ════════ -->
  <aside class="coach-panel">

    <div style="font-size:0.8rem;font-weight:700;color:var(--cyan);letter-spacing:0.5px;padding:4px 2px 6px;">
      👥 Coach Your Team
    </div>

    <!-- Team tabs + role cards -->
    <div class="tabs">
      <button class="tab-btn" id="tab-r" onclick="switchTeam('Red')">
        <span class="badge badge-r">RED</span>
      </button>
      <button class="tab-btn" id="tab-b" onclick="switchTeam('Blue')">
        <span class="badge badge-b">BLUE</span>
      </button>
    </div>
    <div id="role-cards"></div>

  </aside>

  <!-- ════════ MAIN PANEL (right column) ════════ -->
  <div class="main">

    <!-- Score bar above pitch -->
    <div class="score-bar">
      <div class="sb-team red">🔴 Red Team</div>
      <div class="sb-centre">
        <div class="sb-score" id="main-score">0 – 0</div>
        <div style="display:flex;gap:8px;align-items:center;">
          <span class="sb-timer">⏱ <span id="main-timer">90.0</span>s</span>
          <span class="sb-pill waiting" id="main-pill">⏳ WAITING</span>
        </div>
      </div>
      <div class="sb-team blue" style="text-align:right;">Blue Team 🔵</div>
    </div>

    <!-- Pitch canvas -->
    <div class="pitch-wrap">
      <canvas id="pitch" width="1200" height="800"></canvas>
    </div>

    <!-- Coach AI strip below pitch -->
    <div class="coach-strip">
      <span class="coach-strip-label">✨ Tactical Coach AI</span>
      <input type="text" id="coach-in" placeholder="e.g. tiki-taka, park the bus, gegenpressing, total football…"/>
      <button class="btn-gen" onclick="genPlan()">✦ Generate</button>
    </div>

  </div>

</div>

<div id="toast"></div>

<script>
/* ═══════════════════════════════════════════════════
   PITCH CANVAS
═══════════════════════════════════════════════════ */
const canvas = document.getElementById('pitch');
const ctx    = canvas.getContext('2d');
const W = 1200, H = 800, CY = 425;
const TRAIL = [];
const TRAIL_MAX = 16;

let gameState = {
  match_state:'Waiting', time_left:90,
  score:{Red:0,Blue:0}, ball:{x:600,y:CY}, players:{}
};

function drawPitch() {
  // Grass
  const g = ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,   '#174d17');
  g.addColorStop(0.5, '#1b5e1b');
  g.addColorStop(1,   '#174d17');
  ctx.fillStyle = g;
  ctx.fillRect(0,0,W,H);

  // Stripes
  for (let i=0;i<8;i++){
    ctx.fillStyle = i%2===0 ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.025)';
    ctx.fillRect(i*(W/8),0,W/8,H);
  }

  ctx.strokeStyle = 'rgba(255,255,255,0.82)';
  ctx.lineWidth = 2;

  // Boundary
  ctx.strokeRect(3,3,W-6,H-6);

  // Centre line
  ctx.beginPath(); ctx.moveTo(W/2,0); ctx.lineTo(W/2,H); ctx.stroke();

  // Centre circle
  ctx.beginPath(); ctx.arc(W/2,CY,80,0,Math.PI*2); ctx.stroke();

  // Centre dot
  ctx.fillStyle='rgba(255,255,255,0.82)';
  ctx.beginPath(); ctx.arc(W/2,CY,5,0,Math.PI*2); ctx.fill();

  // Penalty areas
  ctx.strokeRect(0,CY-150,120,300);
  ctx.strokeRect(W-120,CY-150,120,300);

  // 6-yard boxes
  ctx.strokeRect(0,CY-60,40,120);
  ctx.strokeRect(W-40,CY-60,40,120);

  // Penalty spots
  ctx.beginPath(); ctx.arc(88,CY,4,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.arc(W-88,CY,4,0,Math.PI*2); ctx.fill();

  // Penalty arcs
  ctx.beginPath(); ctx.arc(88,CY,70,-0.44*Math.PI,0.44*Math.PI); ctx.stroke();
  ctx.beginPath(); ctx.arc(W-88,CY,70,Math.PI*0.56,Math.PI*1.44); ctx.stroke();

  // Corner arcs
  [[0,0,0,Math.PI/2],[W,0,Math.PI/2,Math.PI],[0,H,-Math.PI/2,0],[W,H,Math.PI,1.5*Math.PI]].forEach(([x,y,s,e])=>{
    ctx.beginPath(); ctx.arc(x,y,12,s,e); ctx.stroke();
  });

  // Goals (y 325–525 = CY±100, x 0–30 and W-30–W)
  ctx.fillStyle='rgba(255,215,0,0.18)';
  ctx.strokeStyle='#ffd700'; ctx.lineWidth=2.5;
  ctx.fillRect(0,CY-100,30,200); ctx.strokeRect(0,CY-100,30,200);
  ctx.fillRect(W-30,CY-100,30,200); ctx.strokeRect(W-30,CY-100,30,200);

  ctx.fillStyle='#ffd700'; ctx.font='bold 10px Segoe UI';
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillText('GOAL',15,CY); ctx.fillText('GOAL',W-15,CY);
}

function drawTrail() {
  TRAIL.forEach((p,i)=>{
    const a = (i/TRAIL.length)*0.3;
    const r = 3+(i/TRAIL.length)*5;
    ctx.beginPath(); ctx.arc(p.x,p.y,r,0,Math.PI*2);
    ctx.fillStyle=`rgba(255,255,255,${a})`; ctx.fill();
  });
}

function drawBall(x,y) {
  ctx.beginPath(); ctx.ellipse(x+3,y+5,8,4,0,0,Math.PI*2);
  ctx.fillStyle='rgba(0,0,0,0.25)'; ctx.fill();
  ctx.beginPath(); ctx.arc(x,y,9,0,Math.PI*2);
  ctx.fillStyle='#fff'; ctx.fill();
  ctx.strokeStyle='#222'; ctx.lineWidth=1.5; ctx.stroke();
  ctx.beginPath(); ctx.arc(x,y,4,0,Math.PI*2);
  ctx.fillStyle='#444'; ctx.fill();
}

function drawPlayers(players) {
  Object.entries(players).forEach(([name,pos])=>{
    const isRed = name.startsWith('Red');
    const isGK  = name.includes('Goalkeeper');
    const cx=pos.x, cy=pos.y;

    // Shadow
    ctx.beginPath(); ctx.ellipse(cx+2,cy+4,13,6,0,0,Math.PI*2);
    ctx.fillStyle='rgba(0,0,0,0.2)'; ctx.fill();

    // Body gradient
    const gr = ctx.createRadialGradient(cx-3,cy-3,2,cx,cy,14);
    if(isRed){ gr.addColorStop(0,'#ff7070'); gr.addColorStop(1,'#c81e1e'); }
    else      { gr.addColorStop(0,'#70a8ff'); gr.addColorStop(1,'#1e4fc8'); }
    ctx.beginPath(); ctx.arc(cx,cy,14,0,Math.PI*2);
    ctx.fillStyle=gr; ctx.fill();

    // GK gold ring
    if(isGK){
      ctx.beginPath(); ctx.arc(cx,cy,14,0,Math.PI*2);
      ctx.strokeStyle='#ffd700'; ctx.lineWidth=2.5; ctx.stroke();
    }
    ctx.beginPath(); ctx.arc(cx,cy,14,0,Math.PI*2);
    ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=1.5; ctx.stroke();

    // Initial letter
    const letter = name.replace(/^(Red|Blue)_/,'')[0] || '?';
    ctx.fillStyle='#fff'; ctx.font='bold 12px Segoe UI';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(letter,cx,cy);

    // Name tag
    const label = name.replace(/^(Red|Blue)_/,'');
    ctx.font='10px Segoe UI';
    const tw = ctx.measureText(label).width+8;
    ctx.fillStyle='rgba(0,0,0,0.6)';
    ctx.beginPath(); ctx.roundRect(cx-tw/2,cy+17,tw,13,3); ctx.fill();
    ctx.fillStyle = isRed ? '#fca5a5' : '#93c5fd';
    ctx.textBaseline='top';
    ctx.fillText(label,cx,cy+19);
    ctx.textBaseline='alphabetic';
  });
}

function renderFrame() {
  ctx.clearRect(0,0,W,H);
  drawPitch();
  drawTrail();
  drawBall(gameState.ball.x, gameState.ball.y);
  drawPlayers(gameState.players);

  if(gameState.match_state === 'Waiting'){
    ctx.fillStyle='rgba(0,0,0,0.42)';
    ctx.fillRect(0,0,W,H);
    ctx.fillStyle='#eab308';
    ctx.font='bold 34px Segoe UI'; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText('⏳  WAITING FOR KICK-OFF', W/2, H/2-18);
    ctx.font='17px Segoe UI'; ctx.fillStyle='rgba(255,255,255,0.55)';
    ctx.fillText('Click ▶ Start to begin', W/2, H/2+22);
    ctx.textBaseline='alphabetic';
  }
}

/* ═══════════════════════════════════════════════════
   STATE POLLING
═══════════════════════════════════════════════════ */
async function poll() {
  try {
    const r = await fetch('/api/state');
    if(!r.ok) return;
    const d = await r.json();
    gameState = d;

    TRAIL.push({x:d.ball.x, y:d.ball.y});
    if(TRAIL.length > TRAIL_MAX) TRAIL.shift();

    // Sidebar live bar
    const red=d.score.Red??0, blue=d.score.Blue??0;
    document.getElementById('sb-score').textContent  = red+' – '+blue;
    document.getElementById('sb-timer').textContent  = parseFloat(d.time_left).toFixed(1);
    const playing = d.match_state==='Playing';
    document.getElementById('sb-pill').textContent   = playing ? '🟢 PLAYING' : '⏳ WAITING';

    // Main score bar
    document.getElementById('main-score').textContent = red+' – '+blue;
    document.getElementById('main-timer').textContent  = parseFloat(d.time_left).toFixed(1);
    const mp = document.getElementById('main-pill');
    mp.textContent = playing ? '🟢 PLAYING' : '⏳ WAITING';
    mp.className   = 'sb-pill '+(playing?'playing':'waiting');

    // Server dot
    const dot = document.getElementById('srv-dot');
    dot.style.background = 'var(--green)';
    dot.style.boxShadow  = '0 0 6px var(--green)';

    // Debug
    document.getElementById('debug-con').textContent = JSON.stringify(d, null, 2);

    // Leaderboard
    recordMatch(d.score, d.match_state);
  } catch(e) {
    const dot = document.getElementById('srv-dot');
    dot.style.background='#ef4444'; dot.style.boxShadow='0 0 6px #ef4444';
  }
}

function loop() { renderFrame(); requestAnimationFrame(loop); }
setInterval(poll, 100);
poll();
loop();

/* ═══════════════════════════════════════════════════
   MATCH CONTROLS
═══════════════════════════════════════════════════ */
async function ctrl(action) {
  try {
    const r = await fetch('/api/match/'+action, {method:'POST'});
    const d = await r.json();
    toast(r.ok ? '✓ '+d.message : '✗ '+(d.error||'Error'), r.ok ? 'ok' : 'err');
    await poll();
  } catch(e) { toast('✗ Connection error','err'); }
}

/* ═══════════════════════════════════════════════════
   COACH AI
═══════════════════════════════════════════════════ */
const PLANS = {
  'tiki-taka':     {Striker:'Short one-touch play, stay connected, pressure on loss.',Midfielder:'Keep possession with triangles, press immediately.',Defender:'Build short from back, don\'t lunge.',Goalkeeper:'Short distribution, start build-up calmly.'},
  'park the bus':  {Striker:'Hold up ball, shield possession near corner flags.',Midfielder:'Sit deep, block passing lanes, hard tackles.',Defender:'Compact block, never step out, clear decisively.',Goalkeeper:'Command area, clear long and fast.'},
  'gegenpressing': {Striker:'Press instantly on loss, force errors high.',Midfielder:'Sprint press, win second balls, fast transitions.',Defender:'High line, aggressive, cover with pace.',Goalkeeper:'Sweeper-keeper, rush off line.'},
  'total football':{Striker:'Drop to create overloads, interchange freely.',Midfielder:'Roam all zones, cover any position.',Defender:'Join attacks, be comfortable on ball.',Goalkeeper:'Precise feet, start positional play.'},
  'counter':       {Striker:'Burst behind on possession win.',Midfielder:'Win ball fast, vertical ball immediately.',Defender:'Stay deep, trigger quick vertical pass.',Goalkeeper:'Launch fast on saves.'},
};

function genPlan() {
  if (!curTeam) { toast('Select a team first', 'err'); return; }
  const raw = document.getElementById('coach-in').value.trim().toLowerCase();
  let plan = null;
  for(const [k,v] of Object.entries(PLANS)) if(raw.includes(k)) { plan=v; break; }
  if(!plan) plan = {
    Striker:   raw||'First to every ball, shoot on sight.',
    Midfielder:raw||'Control the tempo, win second balls.',
    Defender:  raw||'Stay compact, protect the goalkeeper.',
    Goalkeeper:raw||'Command your area, distribute quickly.',
  };
  POSITIONS.forEach(p => { promptData[curTeam][p]=plan[p]||plan.Striker; });
  renderRoles();
  toast('✓ Plan generated for '+curTeam, 'ok');
}

/* ═══════════════════════════════════════════════════
   ROLE CARDS
═══════════════════════════════════════════════════ */
const POSITIONS = ['Striker','Midfielder','Defender','Goalkeeper'];
const DEF_PROMPTS = {
  Striker:   'First to every ball. No hesitation. Hit the target — hard.',
  Midfielder:'Control the tempo. Win ball fast, distribute with precision.',
  Defender:  'Stay between ball and goal. Clear danger, support keeper.',
  Goalkeeper:'Command area. Catch everything in range. Distribute quickly.',
};
const TAGS = {
  Striker:   ['🔥 Aggressive','🎯 Sniper','↔ Counter','🤝 Team Player'],
  Midfielder:['⚡ Box-to-Box','🎭 Creative','🛡 Defensive','↔ Counter'],
  Defender:  ['🧱 Solid','📐 Tactical','🚀 Sweeper','↔ Counter'],
  Goalkeeper:['🧤 Shot Stopper','🦵 Sweeper-Keeper','📢 Commander','🎯 Distributor'],
};

let curTeam  = null;   // null until user picks a team
let promptData = {Red:{},Blue:{}};
let selTags    = {Red:{},Blue:{}};
POSITIONS.forEach(p=>{ ['Red','Blue'].forEach(t=>{ promptData[t][p]=DEF_PROMPTS[p]; selTags[t][p]=[]; }); });

function switchTeam(t) {
  saveCurPrompts();
  curTeam = t;
  document.getElementById('tab-r').classList.toggle('active', t==='Red');
  document.getElementById('tab-b').classList.toggle('active', t==='Blue');
  renderRoles();
}

function saveCurPrompts() {
  if (!curTeam) return;
  POSITIONS.forEach(p=>{ const el=document.getElementById('pr-'+p); if(el) promptData[curTeam][p]=el.value; });
}

function renderRoles() {
  const container = document.getElementById('role-cards');
  if (!curTeam) {
    container.innerHTML = '<div style="color:var(--text-muted);font-size:0.75rem;padding:10px 0;text-align:center;">Select a team above to configure players.</div>';
    return;
  }
  const t=curTeam, bc=t==='Red'?'badge-r':'badge-b', bl=t==='Red'?'RED':'BLUE';
  document.getElementById('role-cards').innerHTML = POSITIONS.map((p,i)=>{
    const prompt=promptData[t][p]||'', active=prompt.trim().length>0;
    const tags=TAGS[p]||[], st=selTags[t][p]||[];
    const tagsHtml=tags.map(g=>`<span class="style-tag${st.includes(g)?' sel':''}" onclick="toggleTag('${p}','${esc(g)}')">${esc(g)}</span>`).join('');
    return `<div class="role-card">
      <div class="role-hdr" onclick="toggleRole('rb-${p}','rc-${p}')">
        <div class="role-left">
          <span class="badge ${bc}">${bl}</span>
          <span class="role-title">${p}</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="status-badge ${active?'s-active':'s-inactive'}" id="sb-${p}">${active?'🟢 ACTIVE':'⚪ INACTIVE'}</span>
          <span class="chevron${i===0?' open':''}" id="rc-${p}">▼</span>
        </div>
      </div>
      <div class="role-body${i===0?'':' hidden'}" id="rb-${p}">
        <div class="style-tags" id="tg-${p}">${tagsHtml}</div>
        <textarea class="prompt-area" id="pr-${p}" rows="3"
          oninput="onPrChange('${p}')">${esc(prompt)}</textarea>
        <div style="display:flex;justify-content:flex-end;margin-top:5px;">
          <button class="btn btn-dark" style="font-size:0.65rem;padding:4px 8px;" onclick="clearP('${p}')">✕ Clear</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

function toggleRole(bodyId, chevId) {
  document.getElementById(bodyId)?.classList.toggle('hidden');
  document.getElementById(chevId)?.classList.toggle('open');
}

function onPrChange(p) {
  promptData[curTeam][p] = document.getElementById('pr-'+p).value;
  const b = document.getElementById('sb-'+p);
  if(b){ const a=promptData[curTeam][p].trim().length>0; b.className='status-badge '+(a?'s-active':'s-inactive'); b.textContent=a?'🟢 ACTIVE':'⚪ INACTIVE'; }
}

function clearP(p) { const el=document.getElementById('pr-'+p); if(el){el.value=''; onPrChange(p);} }

function toggleTag(p,tag) {
  const arr=selTags[curTeam][p]||[], idx=arr.indexOf(tag);
  idx>=0?arr.splice(idx,1):arr.push(tag); selTags[curTeam][p]=arr;
  const strip=document.getElementById('tg-'+p); if(!strip) return;
  strip.innerHTML=(TAGS[p]||[]).map(g=>`<span class="style-tag${arr.includes(g)?' sel':''}" onclick="toggleTag('${p}','${esc(g)}')">${esc(g)}</span>`).join('');
}

/* ═══════════════════════════════════════════════════
   STRATEGY LIBRARY
═══════════════════════════════════════════════════ */
let strats = JSON.parse(localStorage.getItem('strats')||'[]');

function saveStrat() {
  const name = document.getElementById('strat-name').value.trim();
  if(!name){toast('Enter a name','err');return;}
  saveCurPrompts();
  strats.push({name,team:curTeam,prompts:JSON.parse(JSON.stringify(promptData[curTeam])),saved:new Date().toLocaleDateString()});
  localStorage.setItem('strats',JSON.stringify(strats));
  document.getElementById('strat-name').value='';
  renderStrats(); toast('✓ Saved: '+name,'ok');
}

function loadStrat(i) {
  const s=strats[i]; if(!s) return;
  curTeam=s.team; promptData[s.team]=JSON.parse(JSON.stringify(s.prompts));
  document.getElementById('tab-r').classList.toggle('active',s.team==='Red');
  document.getElementById('tab-b').classList.toggle('active',s.team==='Blue');
  renderRoles(); toast('✓ Loaded: '+s.name,'ok');
}

function delStrat(i) { strats.splice(i,1); localStorage.setItem('strats',JSON.stringify(strats)); renderStrats(); }

function renderStrats() {
  document.getElementById('strat-count').textContent=strats.length;
  const el=document.getElementById('strat-list');
  el.innerHTML=strats.length===0
    ?'<div class="strategy-item" style="color:var(--text-muted);font-style:italic;">No saved strategies.</div>'
    :strats.map((s,i)=>`<div class="strategy-item" style="display:flex;justify-content:space-between;align-items:center;">
        <span>${esc(s.name)} <span style="color:var(--text-muted);font-size:.65rem;">${s.team}</span></span>
        <span style="display:flex;gap:3px;">
          <button class="btn btn-dark" style="padding:2px 7px;font-size:.65rem;" onclick="loadStrat(${i})">Load</button>
          <button class="btn btn-red"  style="padding:2px 7px;font-size:.65rem;" onclick="delStrat(${i})">✕</button>
        </span>
      </div>`).join('');
}

/* ═══════════════════════════════════════════════════
   LEADERBOARD
═══════════════════════════════════════════════════ */
let lb = JSON.parse(localStorage.getItem('lb')||'[]');
let lastMatchState = 'Waiting';

function recordMatch(score, state) {
  if(lastMatchState==='Playing' && state==='Waiting'){
    const {Red:r=0,Blue:b=0}=score;
    if(r>0||b>0){ lb.push({r,b,d:new Date().toLocaleDateString()}); if(lb.length>20) lb.shift(); localStorage.setItem('lb',JSON.stringify(lb)); renderLb(); }
  }
  lastMatchState=state;
}

function renderLb() {
  document.getElementById('lb-count').textContent=lb.length;
  const el=document.getElementById('lb-list');
  el.innerHTML=lb.length===0
    ?'<div class="strategy-item" style="color:var(--text-muted);font-style:italic;">No matches yet.</div>'
    :[...lb].reverse().map((m,i)=>`<div class="strategy-item" style="display:flex;justify-content:space-between;">
        <span style="color:var(--text-dim);">#${lb.length-i}</span>
        <span><span style="color:#f87171;">${m.r}</span> – <span style="color:#60a5fa;">${m.b}</span></span>
        <span style="color:var(--text-muted);font-size:.65rem;">${m.d}</span>
      </div>`).join('');
}

/* ═══════════════════════════════════════════════════
   UTILS
═══════════════════════════════════════════════════ */
function toggleCard(id) {
  document.getElementById('bd-'+id)?.classList.toggle('hidden');
  document.getElementById('ch-'+id)?.classList.toggle('open');
}

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

let _toastTimer;
function toast(msg, type='ok') {
  const el=document.getElementById('toast');
  el.textContent=msg; el.className='show '+type;
  clearTimeout(_toastTimer); _toastTimer=setTimeout(()=>el.className='',2800);
}

const I18N = {
  es:{ 'Football Soccer – LLM Driven':'Fútbol – Impulsado por LLM', 'Match Setup':'Configuración del Partido',
       'Start':'INICIAR','End':'TERMINAR','Reset Ball':'RESET BALÓN','Reset Match':'RESET PARTIDO' },
  fr:{ 'Match Setup':'Configuration du Match','Start':'DÉMARRER','End':'TERMINER' },
};
function setLang(l) {
  const t=I18N[l]||{};
  document.querySelectorAll('[data-i18n]').forEach(el=>{const k=el.getAttribute('data-i18n'); if(t[k]) el.textContent=t[k];});
}

/* ═══════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════ */
renderRoles();   // shows "select a team" placeholder
renderStrats();
renderLb();
</script>
</body>
</html>
"""
