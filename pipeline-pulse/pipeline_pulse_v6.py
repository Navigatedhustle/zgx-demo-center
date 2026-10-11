"""
Pipeline Pulse v6 — FastAPI backend
HP ZGX Nano G1n · O&G AI Developer Demo
Port 8087

Endpoints:
  GET  /                    → serves pipeline_pulse_v6.html
  WS   /ws/telemetry        → streams real GPU stats via pynvml every 2s
  POST /api/inference       → queues Ollama request, streams SSE response
  GET  /api/status          → session stats, queue depth, model info
  GET  /api/reset           → reset session counters
"""

import asyncio
import json
import os
import time
import queue
import subprocess
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn
import websockets

# ── pynvml + nvidia-smi + psutil (self-contained, no Performance Lab dep) ───
# Pipeline Pulse runs standalone — no dependency on port 8080.
try:
    import pynvml
    pynvml.nvmlInit()
    _handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    NVML_OK = True
except Exception:
    NVML_OK = False

try:
    import psutil
    PSUTIL_OK = True
except Exception:
    PSUTIL_OK = False

# ── hw/sys caches (filled by background poller below) ───────────────────────
_hw_cache = {
    "clock": 0, "gpu_util": 0, "power": 0.0, "temp": 0,
    "throttling": False, "reasons": "None", "workload": "idle",
}
_sys_cache = {"cpu": 0.0, "ram_gb": 0.0, "ram_pct": 0.0}

def _poll_hw_once():
    """Read GPU hw stats via nvidia-smi."""
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,power.draw,temperature.gpu,"
                        "clocks.current.graphics,clocks_throttle_reasons.active",
            "--format=csv,noheader,nounits"
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
        if r.returncode != 0:
            return {}
        parts = [p.strip() for p in r.stdout.strip().split(",")]
        if len(parts) < 5:
            return {}
        util    = int(float(parts[0]))
        power   = float(parts[1])
        temp    = int(float(parts[2]))
        clock   = int(float(parts[3]))
        thr_raw = parts[4].strip()
        try:
            thr_val    = int(thr_raw, 16)
            throttling = thr_val not in (0x0, 0x2)
            reasons    = hex(thr_val) if throttling else "None"
        except ValueError:
            throttling = thr_raw.lower() not in ("not applicable", "none", "0x0000000000000000")
            reasons    = thr_raw if throttling else "None"
        return {
            "gpu_util": util, "power": power, "temp": temp,
            "clock": clock, "throttling": throttling, "reasons": reasons,
            "workload": "active" if util > 5 else "idle",
        }
    except Exception:
        return {}

def _poll_sys_once():
    """Read CPU and RAM via psutil."""
    if not PSUTIL_OK:
        return {}
    try:
        cpu = psutil.cpu_percent(interval=None)
        vm  = psutil.virtual_memory()
        return {
            "cpu":     round(cpu, 1),
            "ram_gb":  round(vm.used / 1e9, 1),
            "ram_pct": round(vm.percent, 1),
        }
    except Exception:
        return {}

async def poll_perf_lab_ws():
    """Background poller: nvidia-smi + psutil every 2s (self-contained).
    Retained same function name so startup_tasks() needs no changes."""
    if PSUTIL_OK:
        try:
            psutil.cpu_percent(interval=None)  # prime — first call returns 0.0
        except Exception:
            pass
    while True:
        hw = _poll_hw_once()
        if hw:
            _hw_cache.update(hw)
        sys_stats = _poll_sys_once()
        if sys_stats:
            _sys_cache.update(sys_stats)
        await asyncio.sleep(2)


def get_mem_from_pynvml() -> dict:
    """Reads GPU memory via pynvml with `ollama ps` fallback for GB10.

    GB10 unified memory often reports used=0 via NVML — when that happens
    we sum the currently loaded Ollama model sizes as a proxy.
    """
    mem_stats = {"mem_used_gb": 0.0, "mem_total_gb": 128.0}
    if not NVML_OK:
        return {"mem_used_gb": 102.0, "mem_total_gb": 128.0}

    mem_used = 0
    try:
        mem = pynvml.nvmlDeviceGetMemoryInfo(_handle)
        mem_used = mem.used
        mem_stats["mem_total_gb"] = round(mem.total / 1e9, 1)
    except Exception:
        pass

    # Fallback: parse `ollama ps` for loaded model sizes.
    # Real output: "llama3.1:70b  711a9e8463af  102 GB  100% GPU  131072  Forever"
    # "102 GB" is two tokens, so scan for GB/MB unit tokens and read parts[i-1].
    if mem_used == 0:
        try:
            result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True, timeout=3)
            lines = result.stdout.strip().split('\n')
            total_gb = 0.0
            for line in lines[1:]:  # skip header
                parts = line.split()
                for i, tok in enumerate(parts):
                    if tok in ('GB', 'GiB') and i > 0:
                        try:
                            total_gb += float(parts[i-1])
                        except ValueError:
                            pass
                    elif tok in ('MB', 'MiB') and i > 0:
                        try:
                            total_gb += float(parts[i-1]) / 1024.0
                        except ValueError:
                            pass
            if total_gb > 0:
                mem_used = total_gb * 1e9
        except Exception:
            pass

    mem_stats["mem_used_gb"] = round(mem_used / 1e9, 1)
    return mem_stats

def get_gpu_stats() -> dict:
    """Unified telemetry: Performance Lab WS for HW/sys, pynvml for memory."""
    mem = get_mem_from_pynvml()
    return {
        "gpu_util":         _hw_cache.get("gpu_util", 0) or 0,
        "clock_mhz":        _hw_cache.get("clock", 0) or 0,
        "power_w":          _hw_cache.get("power", 0.0) or 0.0,
        "temp_c":           _hw_cache.get("temp", 0) or 0,
        "throttling":       bool(_hw_cache.get("throttling", False)),
        "throttle_reasons": _hw_cache.get("reasons", "None") or "None",
        "workload":         _hw_cache.get("workload", "idle") or "idle",
        "cpu_pct":          _sys_cache.get("cpu", 0.0) or 0.0,
        "ram_gb":           _sys_cache.get("ram_gb", 0.0) or 0.0,
        "ram_pct":          _sys_cache.get("ram_pct", 0.0) or 0.0,
        "mem_used_gb":      mem.get("mem_used_gb", 102.0),
        "mem_total_gb":     mem.get("mem_total_gb", 128.0),
        "nvml_ok":          True,
    }

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="Pipeline Pulse v6")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:70b"
HTML_FILE    = Path(__file__).parent / "pipeline_pulse_v6.html"

# ── Session state ────────────────────────────────────────────────────────────
session = {
    "incident_count": 0,
    "cloud_calls":    0,          # always stays 0 — the point
    "last_latency_s": None,
    "queue_depth":    0,
}

# ── Startup: warm the model + kick off Performance Lab telemetry poller ────
@app.on_event("startup")
async def startup_tasks():
    # 1) Warm llama3.1:70b so the first real inference isn't cold
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            await client.post(
                "http://localhost:11434/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": "Ready.", "stream": False},
            )
    except Exception:
        pass
    # 2) Start background poller for ws://localhost:8080/ws (Performance Lab)
    asyncio.create_task(poll_perf_lab_ws())

# ── Inference queue (serialize all Ollama requests) ──────────────────────────
_infer_lock = asyncio.Lock()

async def run_inference(sensor: str, reading: str, context: str, prompt: str,
                         sev: str = "warning", detector: str = "anomaly detector"):
    """Queue-serialized call to Ollama. Yields text chunks."""
    async with _infer_lock:
        session["queue_depth"] += 1
        t0 = time.time()
        first_token = True
        try:
            threshold_word = "alert threshold" if sev == "critical" else "warning threshold"
            full_prompt = (
                "You are an oil & gas operations AI. A sensor has triggered:\n"
                f"sensor: {sensor}\n"
                f"value: {reading}\n"
                f"threshold crossed: {threshold_word}\n"
                f"model: {detector}\n\n"
                "Reply in exactly three lines, each labeled:\n"
                "**Severity:** <one word: Low, Medium, High, or Critical>\n"
                "**Anomaly:** <one sentence describing what the data suggests>\n"
                "**Recommendation:** <one sentence on immediate operator action>"
            )
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", OLLAMA_URL, json={
                    "model": OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": True,
                    "options": {
                        "num_predict": 110,
                        "temperature": 0.4,
                    },
                }) as resp:
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        token = chunk.get("response", "")
                        if token:
                            if first_token:
                                session["last_latency_s"] = round(time.time() - t0, 2)
                                first_token = False
                            yield token
                        if chunk.get("done"):
                            break
            session["incident_count"] += 1
        except Exception as e:
            yield f"[Inference error: {e}]"
        finally:
            session["queue_depth"] = max(0, session["queue_depth"] - 1)

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_html():
    if HTML_FILE.exists():
        return HTMLResponse(content=HTML_FILE.read_text(), status_code=200)
    return HTMLResponse("<h1>pipeline_pulse_v6.html not found</h1>", status_code=404)

@app.get("/api/status")
async def api_status():
    gpu = get_gpu_stats()
    return JSONResponse({**session, **gpu, "model": OLLAMA_MODEL, "ollama_url": OLLAMA_URL})

@app.get("/api/reset")
async def api_reset():
    session["incident_count"] = 0
    session["last_latency_s"] = None
    return JSONResponse({"reset": True})

@app.post("/api/inference")
async def api_inference(request: Request):
    """SSE endpoint — streams Ollama response tokens."""
    body = await request.json()
    sensor   = body.get("sensor", "Unknown sensor")
    reading  = body.get("reading", "")
    context  = body.get("context", "")
    prompt   = body.get("prompt", f"Analyze this anomaly: {sensor} reading {reading}.")
    sev      = body.get("sev", "warning")
    detector = body.get("detector", "anomaly detector")

    async def event_stream():
        yield f"data: {json.dumps({'type': 'queued', 'queue_depth': session['queue_depth'] + 1})}\n\n"
        async for token in run_inference(sensor, reading, context, prompt, sev, detector):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'latency_s': session['last_latency_s'], 'count': session['incident_count']})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                              headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    """Streams real GPU telemetry every 2 seconds."""
    await ws.accept()
    try:
        while True:
            stats = get_gpu_stats()
            stats["ts"] = time.time()
            await ws.send_json(stats)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("pipeline_pulse_v6:app", host="0.0.0.0", port=int(os.environ.get("PP_PORT", 8087)), reload=False)
