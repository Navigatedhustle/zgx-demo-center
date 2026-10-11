"""Single-file HTML/CSS/JS frontend for the AI Vision demo.

Served as a string by vision_demo.py. No build step, no frameworks.
Layout: scenario tab bar → 2x3 video grid + sidebar (stats + alert feed) → class filter row.
"""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>HP ZGX Nano — AI Vision Demo</title>
<style>
  :root{
    --bg:#0a0e17;
    --panel:#101723;
    --panel-2:#0d1420;
    --border:#1b2435;
    --text:#e6edf6;
    --dim:#7c8aa3;
    --accent:#3b82f6;
    --accent-2:#60a5fa;
    --good:#22c55e;
    --warn:#f59e0b;
    --bad:#ef4444;
    --mono:'JetBrains Mono','SF Mono',Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%;width:100%;overflow:hidden}
  body{
    background:var(--bg);color:var(--text);
    font-family:'Inter','Segoe UI',system-ui,sans-serif;
    font-size:13px;
    display:flex;flex-direction:column;
  }
  /* ── Header ───────────────────────────────── */
  .hdr{
    flex:0 0 auto;
    display:flex;align-items:center;gap:18px;
    padding:10px 18px;
    background:linear-gradient(90deg,#0d1726 0%,#0a0e17 70%);
    border-bottom:1px solid var(--border);
    height:54px;
  }
  .hdr-logo{
    width:28px;height:28px;border-radius:50%;
    background:#ffffff;
    display:flex;align-items:center;justify-content:center;
    flex-shrink:0;overflow:hidden;margin-right:10px;
  }
  .hdr-logo img{
    width:36px;height:36px;border-radius:50%;
    object-fit:fill;display:block;
  }
  .hdr-title{font-size:15px;font-weight:600;letter-spacing:-.01em}
  .hdr-sub{font-size:11px;color:var(--dim);margin-top:2px}
  .hdr-spacer{flex:1}
  .hdr-status{
    display:flex;align-items:center;gap:6px;
    padding:5px 10px;border:1px solid var(--border);border-radius:4px;
    font-family:var(--mono);font-size:11px;color:var(--dim);
  }
  .hdr-dot{width:6px;height:6px;border-radius:50%;background:var(--good);box-shadow:0 0 6px var(--good);animation:pulse 2s infinite}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

  /* ── Scenario tabs ────────────────────────── */
  .tabs{
    flex:0 0 auto;
    display:flex;gap:0;padding:0 18px;
    background:var(--panel-2);
    border-bottom:1px solid var(--border);
  }
  .tab{
    padding:10px 18px;cursor:pointer;
    color:var(--dim);font-size:12px;font-weight:500;
    border-bottom:2px solid transparent;
    transition:color .15s,border-color .15s;
    display:flex;align-items:center;gap:8px;
  }
  .tab:hover{color:var(--text)}
  .tab.active{color:var(--accent-2);border-bottom-color:var(--accent)}
  .tab-icon{font-size:14px}
  .tab-desc{color:var(--dim);font-size:11px;margin-left:4px}
  .tab.active .tab-desc{color:var(--text);opacity:.8}

  /* ── Main body ────────────────────────────── */
  .main{
    flex:1;display:grid;
    grid-template-columns:minmax(0,1fr) 320px;
    min-height:0;
    overflow:hidden;
  }
  .grid-wrap{
    padding:14px;display:flex;flex-direction:column;
    min-width:0;overflow:hidden;
  }
  .video-grid{
    flex:1;display:grid;
    grid-template-columns:repeat(3,1fr);
    grid-template-rows:repeat(2,1fr);
    gap:10px;min-height:0;
  }
  .video-grid.enlarged{
    grid-template-columns:1fr;
    grid-template-rows:1fr;
  }
  .stream{
    position:relative;
    background:#000;border:1px solid var(--border);border-radius:6px;
    overflow:hidden;cursor:pointer;
    transition:border-color .15s,box-shadow .15s;
    aspect-ratio:16/9;
    min-height:0;
  }
  .stream:hover{border-color:var(--accent)}
  .stream.hidden{display:none}
  .stream.solo{
    aspect-ratio:auto;
  }
  .stream img{width:100%;height:100%;object-fit:cover;display:block}
  .stream-label{
    position:absolute;top:6px;left:8px;
    padding:3px 8px;border-radius:3px;
    background:rgba(0,0,0,.65);
    font-family:var(--mono);font-size:10px;font-weight:600;
    letter-spacing:.04em;
  }
  .stream-fps{
    position:absolute;top:6px;right:8px;
    padding:3px 8px;border-radius:3px;
    background:rgba(0,0,0,.65);
    font-family:var(--mono);font-size:10px;
    color:var(--good);
  }

  /* ── Sidebar ──────────────────────────────── */
  .sidebar{
    background:var(--panel);
    border-left:1px solid var(--border);
    display:flex;flex-direction:column;
    min-height:0;overflow:hidden;
  }
  .panel{
    border-bottom:1px solid var(--border);
    padding:14px 16px;
  }
  .panel-title{
    font-size:10px;font-weight:600;color:var(--dim);
    text-transform:uppercase;letter-spacing:.08em;
    margin-bottom:10px;
  }
  .stat-row{
    display:flex;justify-content:space-between;align-items:baseline;
    padding:5px 0;
  }
  .stat-key{color:var(--dim);font-size:11px}
  .stat-val{font-family:var(--mono);font-size:13px;color:var(--text)}
  .stat-val.big{font-size:24px;font-weight:600;color:var(--accent-2)}
  .stat-val.good{color:var(--good)}

  .alerts-wrap{
    flex:1;display:flex;flex-direction:column;
    min-height:0;
  }
  .alerts-hdr{
    padding:14px 16px 8px;
    display:flex;justify-content:space-between;align-items:center;
  }
  .alerts-list{
    flex:1;padding:0 12px 14px;overflow-y:auto;
    display:flex;flex-direction:column;gap:8px;
  }
  .alerts-list::-webkit-scrollbar{width:6px}
  .alerts-list::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
  .alert{
    padding:10px 12px;
    background:var(--panel-2);
    border:1px solid var(--border);border-left:3px solid var(--warn);
    border-radius:4px;
    animation:slidein .25s ease-out;
  }
  .alert.critical{border-left-color:var(--bad)}
  @keyframes slidein{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
  .alert-meta{
    display:flex;justify-content:space-between;align-items:center;
    font-family:var(--mono);font-size:10px;color:var(--dim);
    margin-bottom:6px;
  }
  .alert-stream{color:var(--accent-2);font-weight:600}
  .alert-rule{
    font-size:11px;font-weight:600;color:var(--text);
    margin-bottom:4px;
  }
  .alert-text{
    font-size:12px;color:var(--text);line-height:1.5;
    min-height:1.5em;
  }
  .alert-text.streaming::after{
    content:'▮';color:var(--accent);animation:blink 1s infinite;
    margin-left:2px;
  }
  @keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
  .alert-empty{
    text-align:center;padding:20px 12px;color:var(--dim);font-size:11px;
  }

  /* ── Class filter bar ─────────────────────── */
  .filter-bar{
    flex:0 0 auto;
    background:var(--panel-2);
    border-top:1px solid var(--border);
    padding:8px 18px;
    display:flex;align-items:center;gap:8px;flex-wrap:wrap;
    min-height:42px;
  }
  .filter-label{
    font-size:10px;color:var(--dim);font-weight:600;
    text-transform:uppercase;letter-spacing:.08em;
    margin-right:4px;
  }
  .chip{
    padding:4px 10px;border-radius:11px;
    background:transparent;border:1px solid var(--border);
    color:var(--dim);font-size:11px;cursor:pointer;
    transition:all .12s;
    user-select:none;
  }
  .chip:hover{border-color:var(--accent);color:var(--text)}
  .chip.active{
    background:rgba(59,130,246,.15);
    border-color:var(--accent);
    color:var(--accent-2);
  }
  .chip-count{
    margin-left:5px;font-family:var(--mono);font-size:10px;color:var(--dim);
  }
  .chip.active .chip-count{color:var(--accent-2)}

  /* ── Loading overlay ──────────────────────── */
  .loader{
    position:fixed;inset:0;
    background:rgba(10,14,23,.85);
    display:none;align-items:center;justify-content:center;
    z-index:1000;
    font-size:14px;color:var(--accent-2);
  }
  .loader.show{display:flex}
  /* Scenario buttons while a switch is in progress: visually locked. Not
     pointer-events:none — a click still registers so it can update the latest
     queued target (coalescing), it just won't fire another switch. */
  #tabs.locked .tab{opacity:.45;cursor:not-allowed;}
  .loader-spinner{
    width:32px;height:32px;
    border:3px solid var(--border);border-top-color:var(--accent);
    border-radius:50%;
    animation:spin 1s linear infinite;
    margin-right:12px;
  }
  @keyframes spin{to{transform:rotate(360deg)}}

  .badge-zero{
    display:inline-block;padding:2px 6px;
    background:rgba(34,197,94,.15);color:var(--good);
    border-radius:3px;font-family:var(--mono);font-size:10px;font-weight:600;
    margin-left:6px;
  }
</style>
</head>
<body>

<div class="hdr">
  <div class="hdr-logo"><img src="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22%3E%3Crect width=%2264%22 height=%2264%22 fill=%22%23004bdf%22/%3E%3C/svg%3E" alt="HP"></div>
  <div>
    <div class="hdr-title">HP ZGX Nano — AI Vision</div>
    <div class="hdr-sub">Powered by NVIDIA GB10 Blackwell · YOLOv8s TRT FP16</div>
  </div>
  <div class="hdr-spacer"></div>
  <div class="hdr-status"><span class="hdr-dot"></span><span>llama3.1:70b · localhost:11434</span></div>
  <div class="hdr-status"><span class="hdr-dot" style="background:var(--accent)"></span><span id="hdr-qps">0 QPS</span></div>
</div>

<div class="tabs" id="tabs"></div>

<div class="main">
  <div class="grid-wrap">
    <div class="video-grid" id="grid"></div>
  </div>
  <aside class="sidebar">
    <div class="panel">
      <div class="panel-title">Aggregate Throughput</div>
      <div class="stat-row"><span class="stat-key">QPS (all streams)</span><span class="stat-val big" id="agg-qps">0</span></div>
      <div class="stat-row"><span class="stat-key">Latency p50</span><span class="stat-val" id="agg-p50">— ms</span></div>
      <div class="stat-row"><span class="stat-key">Latency p99</span><span class="stat-val" id="agg-p99">— ms</span></div>
      <div class="stat-row"><span class="stat-key">Cloud API Calls</span><span class="stat-val good" id="cloud-calls">0<span class="badge-zero">ZERO</span></span></div>
    </div>
    <div class="panel">
      <div class="panel-title">GPU Telemetry</div>
      <div class="stat-row"><span class="stat-key">Temperature</span><span class="stat-val" id="hw-temp">—</span></div>
      <div class="stat-row"><span class="stat-key">Power Draw</span><span class="stat-val" id="hw-power">—</span></div>
      <div class="stat-row"><span class="stat-key">Clock</span><span class="stat-val" id="hw-clock">—</span></div>
      <div class="stat-row"><span class="stat-key">Utilization</span><span class="stat-val" id="hw-util">—</span></div>
    </div>
    <div class="panel">
      <div class="panel-title">Per-Stream FPS</div>
      <div id="per-stream-list"></div>
    </div>
    <div class="alerts-wrap">
      <div class="alerts-hdr">
        <div class="panel-title" style="margin:0">AI Incident Feed</div>
        <span class="stat-key" style="font-size:10px" id="alert-count">0 events</span>
      </div>
      <div class="alerts-list" id="alerts-list">
        <div class="alert-empty">Monitoring streams. Alerts will appear here when scenario rules trigger.</div>
      </div>
    </div>
  </aside>
</div>

<div class="filter-bar">
  <span class="filter-label">Show classes:</span>
  <span id="filter-chips"></span>
</div>

<div class="loader" id="loader"><div class="loader-spinner"></div><span id="loader-text">Loading scenario…</span></div>

<script>
const STATE = {
  scenarios: [],
  active: null,
  classFilter: new Set(),  // empty = show all
  classCounts: {},
  enlargedStream: null,
  alertSet: new Set(),
  frameWS: null,
  telemWS: null,
  frameWsDeliberate: false,
  telemWsDeliberate: false,
  pendingSwitch: null,    // scenario id awaiting backend ack via /ws
  switchFailsafe: null,   // setTimeout id for the 10s ack-deadline
  switchInProgress: false,// a switch is mid-flight (overlay up, buttons locked)
  queuedTarget: null,     // latest target clicked DURING a switch (coalesced)
  awaitingFirstFrame: false, // backend acked; dismiss overlay on the next real frame
  switchStartedAt: 0,     // Date.now() when the current switch began (overlay-unstick guard)
};

// ── Init ────────────────────────────────────────────
async function init(){
  const r = await fetch('/api/scenarios');
  const d = await r.json();
  STATE.scenarios = d.scenarios;
  STATE.active = d.active || (d.scenarios[0] && d.scenarios[0].id);
  renderTabs();
  applyScenario(STATE.active, /*skipApi*/true);
  connectWS();
  connectFrameWS();
}

// ── Tabs ────────────────────────────────────────────
function renderTabs(){
  const el = document.getElementById('tabs');
  el.innerHTML = '';
  STATE.scenarios.forEach(s => {
    const t = document.createElement('div');
    t.className = 'tab' + (s.id === STATE.active ? ' active' : '');
    t.dataset.id = s.id;
    t.innerHTML =
      `<span class="tab-icon">${s.icon}</span>` +
      `<span>${escapeHtml(s.label)}</span>` +
      `<span class="tab-desc">— ${escapeHtml(s.description)}</span>`;
    t.onclick = () => switchScenario(s.id);
    el.appendChild(t);
  });
}

// Transparent 1x1 GIF — placeholder for <img> tags before the first WS frame
// arrives for that stream id.
const BLANK_GIF = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

function scenarioName(id){
  const s = (STATE.scenarios || []).find(x => x.id === id);
  return (s && s.label) || id;
}

// Lock/unlock the scenario buttons during a switch. We DIM them (not pointer-
// events:none) so a click still registers — but switchScenario only records it as
// the latest queued target rather than firing another switch (coalescing).
function setTabsEnabled(on){
  const tabs = document.getElementById('tabs');
  if (tabs) tabs.classList.toggle('locked', !on);
}

// End-of-switch: drop the overlay, re-enable the buttons, and — if the user clicked
// a different scenario WHILE the switch ran — apply that latest target now.
function finishSwitch(){
  if (STATE.switchFailsafe){ clearTimeout(STATE.switchFailsafe); STATE.switchFailsafe = null; }
  STATE.switchInProgress = false;
  STATE.awaitingFirstFrame = false;
  STATE.pendingSwitch = null;
  hideLoader();
  setTabsEnabled(true);
  const q = STATE.queuedTarget; STATE.queuedTarget = null;
  if (q && q !== STATE.active) switchScenario(q);
}

function switchScenario(id){
  // Coalesce: while a switch is mid-flight, a click only updates the LATEST target.
  // A button-masher can never stack switches — only the last choice is applied,
  // once the current transition completes.
  if (STATE.switchInProgress){
    STATE.queuedTarget = id;
    document.getElementById('loader-text').textContent =
      'Loading ' + scenarioName(id) + ' Video Feed…';
    return;
  }
  if (id === STATE.active) return;
  if (!STATE.telemWS || STATE.telemWS.readyState !== WebSocket.OPEN){
    // Telemetry socket isn't up yet — can't send the command.
    showLoader('Loading ' + scenarioName(id) + ' Video Feed…');
    document.getElementById('loader-text').textContent =
      'Telemetry socket not ready — please retry';
    setTimeout(hideLoader, 2500);
    return;
  }
  // Begin the transition: overlay UP + buttons LOCKED immediately.
  STATE.switchInProgress = true;
  STATE.awaitingFirstFrame = false;
  STATE.queuedTarget = null;
  STATE.pendingSwitch = id;
  STATE.switchStartedAt = Date.now();
  showLoader('Loading ' + scenarioName(id) + ' Video Feed…');
  setTabsEnabled(false);
  // Failsafe: if no {switched:true} ack arrives within 10s, give up and unlock.
  STATE.switchFailsafe = setTimeout(() => {
    STATE.switchFailsafe = null;
    document.getElementById('loader-text').textContent =
      'Scenario switch timed out — backend did not respond';
    setTimeout(finishSwitch, 1500);
  }, 10000);
  try {
    STATE.telemWS.send(JSON.stringify({switch: id}));
  } catch(e){
    console.warn('scenario switch send err', e);
    document.getElementById('loader-text').textContent =
      'Scenario switch failed: ' + (e.message || 'send error');
    setTimeout(finishSwitch, 1500);
  }
}

function applyScenario(id, skipApi){
  STATE.active = id;
  STATE.classFilter = new Set();  // reset filters per scenario
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.id === id);
  });
  renderGrid();
  renderClassFilter();
  if (STATE.enlargedStream !== null){
    STATE.enlargedStream = null;
  }
}

// ── Video grid ──────────────────────────────────────
// All streams are multiplexed over a single WebSocket (/ws/frames). Frame
// arrivals bind to <img id="stream-img-{sid}"> by id, so renderGrid only
// needs to lay out the <img> tags — frame delivery is independent.
function renderGrid(){
  const grid = document.getElementById('grid');
  grid.innerHTML = '';
  grid.classList.remove('enlarged');
  const cfg = STATE.scenarios.find(s => s.id === STATE.active);
  if (!cfg) return;
  const n = cfg.stream_count || 6;
  for (let i = 0; i < n; i++){
    const div = document.createElement('div');
    div.className = 'stream';
    div.dataset.sid = i;
    div.onclick = () => toggleEnlarge(i);
    div.innerHTML =
      `<img id="stream-img-${i}" src="${BLANK_GIF}" alt="Stream ${i+1}" loading="eager">` +
      `<div class="stream-label">S${(i+1).toString().padStart(2,'0')}</div>` +
      `<div class="stream-fps" id="fps-${i}">— fps</div>`;
    grid.appendChild(div);
  }
}

function toggleEnlarge(sid){
  const grid = document.getElementById('grid');
  if (STATE.enlargedStream === sid){
    STATE.enlargedStream = null;
    grid.classList.remove('enlarged');
    document.querySelectorAll('.stream').forEach(el => {
      el.classList.remove('hidden');
      el.classList.remove('solo');
    });
  } else {
    STATE.enlargedStream = sid;
    grid.classList.add('enlarged');
    document.querySelectorAll('.stream').forEach(el => {
      const id = parseInt(el.dataset.sid);
      el.classList.toggle('hidden', id !== sid);
      el.classList.toggle('solo', id === sid);
    });
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && STATE.enlargedStream !== null){
    toggleEnlarge(STATE.enlargedStream);
  }
});

// ── Class filter chips ──────────────────────────────
function renderClassFilter(){
  const wrap = document.getElementById('filter-chips');
  wrap.innerHTML = '';
  const cfg = STATE.scenarios.find(s => s.id === STATE.active);
  if (!cfg) return;
  cfg.relevant_class_names.forEach((name, idx) => {
    const chip = document.createElement('span');
    chip.className = 'chip active';   // default: show all
    chip.dataset.cls = name;
    chip.innerHTML = escapeHtml(name) + `<span class="chip-count" id="cc-${name}">0</span>`;
    chip.onclick = () => {
      // empty filter set means "show all" — clicking once locks the chip set
      if (STATE.classFilter.size === 0){
        cfg.relevant_class_names.forEach(n => STATE.classFilter.add(n));
      }
      if (STATE.classFilter.has(name)){
        STATE.classFilter.delete(name);
        chip.classList.remove('active');
      } else {
        STATE.classFilter.add(name);
        chip.classList.add('active');
      }
      // if everything is on again, clear the explicit set so default-show-all returns
      if (STATE.classFilter.size === cfg.relevant_class_names.length){
        STATE.classFilter = new Set();
      }
    };
    wrap.appendChild(chip);
  });
}

function updateClassChipCounts(counts){
  const cfg = STATE.scenarios.find(s => s.id === STATE.active);
  if (!cfg) return;
  cfg.relevant_class_names.forEach(name => {
    const el = document.getElementById('cc-' + name);
    if (el) el.textContent = counts[name] || 0;
  });
}

// ── WebSocket telemetry ─────────────────────────────
function connectWS(){
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${location.host}/ws`);
  STATE.telemWS = ws;
  // Periodic recycle: every 500 messages, close & reconnect to prevent any
  // per-connection buffer accumulation in the browser. Deliberate flag tells
  // onclose to reconnect quickly rather than treat it as an unexpected drop.
  let msgCount = 0;
  ws.onmessage = ev => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch(e){ return; }
    // Scenario-switch ack from the backend (response to {switch: id} we sent earlier).
    if (msg.switched === true && msg.scenario){
      if (STATE.switchFailsafe){ clearTimeout(STATE.switchFailsafe); STATE.switchFailsafe = null; }
      STATE.pendingSwitch = null;
      applyScenario(msg.scenario, true);
      // Don't drop the overlay on a timer — keep it up until the FIRST real frame of
      // the new scenario actually arrives over /ws/frames (finishSwitch is called
      // from the frame handler). Honest: as fast as the switch truly is, no early
      // dismiss onto a frozen/old frame.
      STATE.awaitingFirstFrame = true;
    } else if (msg.switched === false){
      document.getElementById('loader-text').textContent =
        'Scenario switch rejected: ' + (msg.error || 'unknown error');
      setTimeout(finishSwitch, 2000);
    }
    if (msg.type === 'telemetry') applyTelemetry(msg);
    msgCount++;
    if (msgCount >= 500) {
      msgCount = 0;
      STATE.telemWsDeliberate = true;
      try { ws.close(); } catch(e){}
    }
  };
  ws.onclose = () => {
    if (STATE.telemWS === ws) STATE.telemWS = null;
    const wasDeliberate = STATE.telemWsDeliberate;
    STATE.telemWsDeliberate = false;
    setTimeout(connectWS, wasDeliberate ? 100 : 1000);
  };
  ws.onerror = () => {};
}

// ── WebSocket video frames ──────────────────────────
// Single connection multiplexes all streams. Each binary message is one frame:
// byte 0 = stream_id, bytes 1.. = JPEG. Frames are assigned as base64 data URLs
// directly — no blob URL lifecycle to manage, so nothing accumulates across
// scenario switches.
function connectFrameWS(){
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${location.host}/ws/frames`);
  ws.binaryType = 'arraybuffer';
  STATE.frameWS = ws;
  ws.onmessage = ev => {
    if (typeof ev.data === 'string') return;
    const buf = new Uint8Array(ev.data);
    if (buf.byteLength < 2) return;
    const sid = buf[0];
    const img = document.getElementById('stream-img-' + sid);
    if (!img) return;
    const jpegBytes = new Uint8Array(ev.data, 1);
    let bin = '';
    for (let i = 0; i < jpegBytes.length; i++) {
      bin += String.fromCharCode(jpegBytes[i]);
    }
    img.src = 'data:image/jpeg;base64,' + btoa(bin);
    // First real frame after a switch (backend resumes delivery only once the new
    // scenario has decoded a frame) → drop the overlay + unlock buttons now.
    if (STATE.awaitingFirstFrame){ finishSwitch(); }
  };
  ws.onclose = () => {
    if (STATE.frameWS === ws) STATE.frameWS = null;
    if (STATE.frameWsDeliberate) {
      STATE.frameWsDeliberate = false;
      return;  // switchScenario will reopen
    }
    setTimeout(connectFrameWS, 1000);
  };
  ws.onerror = () => {};
}

function applyTelemetry(msg){
  const m = msg.metrics || {};
  const hw = msg.hw || {};
  // Overlay watchdog: if we're showing the switch overlay but the backend reports it
  // is no longer switching, drop the overlay so it can never get stuck. msg.switch_stalled
  // means the backend watchdog force-resumed a hung switch — clear immediately. Otherwise
  // only clear after a >3s grace (the happy path normally clears on the first frame well
  // before then; the >3s guard avoids racing the brief click→switch-start window).
  if (STATE.switchInProgress && msg.switching === false){
    if (msg.switch_stalled){
      finishSwitch();
    } else if (!STATE.awaitingFirstFrame && (Date.now() - STATE.switchStartedAt) > 3000){
      finishSwitch();
    }
  }
  // Sync active scenario if backend differs (e.g. external API call switched it)
  if (m.scenario && m.scenario !== STATE.active){
    applyScenario(m.scenario, true);
  }
  // Aggregates
  document.getElementById('agg-qps').textContent = (m.total_qps || 0).toFixed(1);
  document.getElementById('hdr-qps').textContent = `${(m.total_qps || 0).toFixed(1)} QPS`;
  document.getElementById('agg-p50').textContent = (m.lat_p50_ms || 0).toFixed(1) + ' ms';
  document.getElementById('agg-p99').textContent = (m.lat_p99_ms || 0).toFixed(1) + ' ms';
  // HW
  document.getElementById('hw-temp').textContent  = hw.temp_c   != null ? hw.temp_c + '°C' : '—';
  document.getElementById('hw-power').textContent = hw.power_w  != null ? hw.power_w.toFixed(1) + ' W' : '—';
  document.getElementById('hw-clock').textContent = hw.clock_mhz != null ? hw.clock_mhz + ' MHz' : '—';
  document.getElementById('hw-util').textContent  = hw.util_pct != null ? hw.util_pct + ' %' : 'N/A';
  // Per-stream FPS list + grid badges
  const list = document.getElementById('per-stream-list');
  list.innerHTML = '';
  (m.streams || []).forEach(s => {
    const row = document.createElement('div');
    row.className = 'stat-row';
    row.innerHTML = `<span class="stat-key" style="color:${s.color}">${s.label}</span>` +
                    `<span class="stat-val">${s.fps.toFixed(1)} fps</span>`;
    list.appendChild(row);
    const fpsBadge = document.getElementById('fps-' + s.id);
    if (fpsBadge) fpsBadge.textContent = s.fps.toFixed(1) + ' fps';
  });
  // Class counts
  STATE.classCounts = m.class_counts || {};
  updateClassChipCounts(STATE.classCounts);
  // New alerts
  (msg.new_alerts || []).forEach(a => {
    if (STATE.alertSet.has(a.id)) return;
    STATE.alertSet.add(a.id);
    addAlert(a);
  });
}

// ── Alert feed + LLM streaming ──────────────────────
function addAlert(a){
  const list = document.getElementById('alerts-list');
  const empty = list.querySelector('.alert-empty');
  if (empty) empty.remove();

  const div = document.createElement('div');
  div.className = 'alert';
  if ((a.rule || '').match(/(critical|forklift|pedestrian|vehicle_in)/)) div.classList.add('critical');
  div.id = 'el-' + a.id;
  div.innerHTML =
    `<div class="alert-meta">` +
      `<span class="alert-stream">${escapeHtml(a.stream_label || ('S' + (a.stream_id+1)))}</span>` +
      `<span>${escapeHtml((a.timestamp||'').slice(11,19))}</span>` +
    `</div>` +
    `<div class="alert-rule">${escapeHtml(a.message || a.rule || 'Alert')}</div>` +
    `<div class="alert-text streaming" id="txt-${a.id}"></div>`;
  list.insertBefore(div, list.firstChild);
  // cap to 30 cards
  while (list.children.length > 30) list.removeChild(list.lastChild);
  document.getElementById('alert-count').textContent = STATE.alertSet.size + ' events';
  // Kick off the LLM brief
  streamBrief(a);
}

function streamBrief(a){
  const target = document.getElementById('txt-' + a.id);
  if (!target) return;
  fetch('/api/alert', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      scenario: a.scenario,
      stream_id: a.stream_id,
      message: a.message,
      class_counts: a.class_counts,
      timestamp: a.timestamp,
    })
  }).then(async resp => {
    if (!resp.ok || !resp.body){
      target.classList.remove('streaming');
      target.textContent = '[brief unavailable]';
      return;
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    while (true){
      const {done, value} = await reader.read();
      if (done) break;
      buf += decoder.decode(value, {stream:true});
      // SSE parse
      let idx;
      while ((idx = buf.indexOf('\n\n')) >= 0){
        const block = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        let evType = 'message', dataStr = '';
        block.split('\n').forEach(line => {
          if (line.startsWith('event:')) evType = line.slice(6).trim();
          else if (line.startsWith('data:')) dataStr += line.slice(5).trim();
        });
        if (!dataStr) continue;
        let payload;
        try { payload = JSON.parse(dataStr); } catch(e){ continue; }
        if (evType === 'token' && payload.text){
          target.textContent += payload.text;
        } else if (evType === 'done'){
          target.classList.remove('streaming');
        } else if (evType === 'error'){
          target.classList.remove('streaming');
          if (!target.textContent) target.textContent = '[brief error: ' + (payload.message || 'unknown') + ']';
        }
      }
    }
    target.classList.remove('streaming');
  }).catch(e => {
    target.classList.remove('streaming');
    target.textContent = '[brief error]';
  });
}

// ── Helpers ─────────────────────────────────────────
function escapeHtml(s){ return String(s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function showLoader(text){
  document.getElementById('loader-text').textContent = text || 'Loading…';
  document.getElementById('loader').classList.add('show');
}
function hideLoader(){ document.getElementById('loader').classList.remove('show'); }

init();
</script>
<script>
// Demo Center iframe escape relay
(function() {
  if (window.parent === window) return; // not iframed, do nothing
  window.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      window.parent.postMessage({ type: 'demo-shell-return' }, '*');
    }
  });
})();
</script>
</body>
</html>
"""
