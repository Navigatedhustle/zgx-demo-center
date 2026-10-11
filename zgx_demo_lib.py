"""
HP ZGX Nano — shared demo helpers.

Generic utilities used by demo_install_server.py for status checks,
SSE streaming, subprocess execution, and Ollama/HTTP probes. Per-demo
data lives in INSTALL_PLANS in the install server; this module is
demo-agnostic.
"""

import asyncio
import json
import socket
from pathlib import Path

# Emit a heartbeat line if a streamed command produces no output for this long
# (Fix 3) — long downloads/builds that go quiet otherwise look hung.
HEARTBEAT_SECONDS = 30


def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _dir_size_gb(path: Path) -> float:
    """Best-effort sum of file sizes under `path`, in GiB (0.0 if absent)."""
    total = 0
    try:
        for p in path.rglob("*"):
            try:
                if p.is_file():
                    total += p.stat().st_size
            except OSError:
                pass
    except OSError:
        pass
    return total / (1024 ** 3)


def _heartbeat_line(heartbeat: dict | None, elapsed_s: float) -> str:
    """Build the periodic 'still alive' line for a quiet long-running step.

    With a `heartbeat` config ({"label", "path", optional "total_gb"}) it reports
    bytes-on-disk so far (e.g. "pharmacy model: 12.4/28 GB downloaded so far …");
    otherwise it's a generic elapsed-time heartbeat (covers docker builds).
    """
    mins, secs = int(elapsed_s // 60), int(elapsed_s % 60)
    et = f"{mins}m{secs:02d}s"
    if heartbeat and heartbeat.get("path"):
        gb = _dir_size_gb(Path(heartbeat["path"]).expanduser())
        label = heartbeat.get("label", "download")
        total = heartbeat.get("total_gb")
        if total:
            return f"⏳ {label}: {gb:.1f}/{total} GB downloaded so far ({et} elapsed)"
        return f"⏳ {label}: {gb:.1f} GB downloaded so far ({et} elapsed)"
    return f"⏳ still working — {et} elapsed (no output yet)"


async def stream_command(cmd: str, cwd, new_session: bool = False,
                         heartbeat: dict | None = None):
    """Run a shell command and stream output line by line.

    new_session=True detaches the child into its own session so a client
    disconnect (which cancels this generator) cannot SIGTERM the launched
    process group — used by /start so backgrounded demos survive.

    heartbeat (Fix 3): when the command emits no line for HEARTBEAT_SECONDS, yield
    a synthetic progress/keep-alive line instead of going silent. Pass a dict
    {"label", "path", "total_gb"?} for a download to report on-disk size so far;
    pass None and any quiet step still gets a generic elapsed-time heartbeat.
    """
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=cwd,
        start_new_session=new_session,
    )
    loop = asyncio.get_event_loop()
    start = loop.time()
    while True:
        try:
            line = await asyncio.wait_for(
                proc.stdout.readline(), timeout=HEARTBEAT_SECONDS
            )
        except asyncio.TimeoutError:
            # No output for HEARTBEAT_SECONDS — surface a heartbeat and keep waiting.
            # readline()'s internal buffer is preserved across the cancelled wait,
            # so no bytes are lost.
            yield _heartbeat_line(heartbeat, loop.time() - start)
            continue
        if not line:
            break
        yield line.decode(errors="replace").rstrip()
    await proc.wait()


async def check_ollama_model(model_tag: str) -> bool:
    """Return True if Ollama is reachable AND has the named model loaded."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code != 200:
                return False
            data = resp.json()
            for m in data.get("models", []) or []:
                name = m.get("name", "")
                if name == model_tag or name.startswith(model_tag):
                    return True
            return False
    except Exception:
        return False


async def check_port_alive(port: int, timeout: float = 1.0) -> bool:
    """Return True if 127.0.0.1:port accepts a TCP connection within `timeout` seconds."""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False


async def check_http_health(url: str, timeout: float = 3.0) -> dict:
    """GET url and return readiness in the legacy minimalist shape.

    Mirrors the original health_check route exactly:
      - HTTP 200            → {"ready": True}
      - any other status    → {"ready": False}    (no extra keys)
      - exception           → {"ready": False, "error": str(e)}
    """
    import httpx
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            return {"ready": resp.status_code == 200}
    except Exception as e:
        return {"ready": False, "error": str(e)}


async def check_files_and_model(
    file_paths: list[str],
    ollama_model: str,
    path: str | None = None,
) -> dict:
    """Generic readiness check: all files exist AND Ollama has the model.

    Return shape mirrors the legacy _check_pipeline_status /
    _check_vision_status payloads:
        {
          "installed": bool,
          "model_ok": bool,
          "files_ok": bool,
          "checks": {<file_key>: bool, ..., "ollama_<model>": bool},
          "path": str,
        }
    Each file_key is the input path with a leading "~/" stripped, so
    "~/pipeline_pulse_v6.py" → "pipeline_pulse_v6.py" and
    "~/zgx_videos/video1.mp4" → "zgx_videos/video1.mp4". The "path"
    field defaults to the first file's expanded location; pass `path`
    to override (vision uses a parent directory, not a file).
    """
    checks: dict[str, bool] = {}
    files_ok = True
    for p in file_paths:
        expanded = Path(p).expanduser()
        ok = expanded.exists()
        if not ok:
            files_ok = False
        key = p[2:] if p.startswith("~/") else p
        checks[key] = ok

    model_ok = await check_ollama_model(ollama_model)
    checks[f"ollama_{ollama_model}"] = model_ok

    if path is not None:
        path_str = str(Path(path).expanduser())
    elif file_paths:
        path_str = str(Path(file_paths[0]).expanduser())
    else:
        path_str = ""

    return {
        "installed": files_ok and model_ok,
        "model_ok": model_ok,
        "files_ok": files_ok,
        "checks": checks,
        "path": path_str,
    }
