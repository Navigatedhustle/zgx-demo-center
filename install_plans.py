#!/usr/bin/env python3
"""
HP ZGX Nano — Demo Center install plans (shared data module).

Single source of truth for the per-demo install/launch/teardown/discovery
metadata. Imported by both demo_install_server.py (the SSE install server)
and install.py (the install orchestrator) so they never diverge.

This module is PURE DATA — it defines no behavior and intentionally imports
nothing from demo_install_server.py (avoids a circular import).
"""

# ── Install sequences per demo ─────────────────────────────────────────────
INSTALL_PLANS = {
    "maritime": {
        "name": "Maritime Surveillance Intelligence",
        "dir": "Fed-Navy-containerized-docker",
        "steps": [
            {"label": "Source vendored — no clone needed", "cmd": "echo 'Source vendored in monorepo — skipping upstream clone.'"},
            {"label": "Downloading model (~9GB — Qwen3-VL-8B FP8)", "cmd": "cd {dir} && bash ./download_models.sh",
             "heartbeat": {"label": "maritime model", "path": "{dir}/models/Qwen3-VL-8B-Instruct-FP8", "total_gb": 11}},
            {"label": "Building Docker container", "cmd": "cd {dir} && docker compose build"},
        ],
        "launch_cmd": "cd {dir} && bash ./start.sh -d",
        "port": 8000,
        "health_url": "http://localhost:8000/api/health",
        "teardown_strategy": {"type": "docker_compose"},
        "discovery": {"type": "docker_container", "patterns": ["maritime", "navy"]},
    },
    "medical": {
        "name": "Robotic Medical Triage Voice Agent",
        "dir": "Robotic-medical-AI-assistant",
        "steps": [
            {"label": "Source vendored — no clone needed", "cmd": "echo 'Source vendored in monorepo — skipping upstream clone.'"},
            {"label": "Downloading models (~4GB — Llama 3.1 8B AWQ + Piper TTS)", "cmd": "cd {dir} && bash ./scripts/download_models.sh 2>/dev/null || python3 -c \"from huggingface_hub import snapshot_download; snapshot_download('hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4', local_dir='models/Llama-3.1-8B-Instruct-AWQ-INT4')\"",
             "heartbeat": {"label": "medical models", "path": "{dir}/models", "total_gb": 4}},
            {"label": "Building Docker image (~10 min — compiles whisper.cpp CUDA)", "cmd": "cd {dir}/docker && docker build --no-cache -t consent-agent:latest -f Dockerfile.api ."},
        ],
        "launch_cmd": "cd {dir}/scripts && bash ./start_services.sh",
        "port": 8090,
        "note": "Requires Pollen Reachy Mini robot on same network.",
        "health_url": "http://localhost:8090/health",
        "teardown_strategy": {"type": "docker_compose"},
        "discovery": {"type": "docker_container", "patterns": ["consent", "medical"]},
    },
    "pharmacy": {
        "name": "Clinical Drug Interaction Analysis",
        "dir": "healthcare-pharmacy-containerized-docker",
        "steps": [
            {"label": "Source vendored — no clone needed", "cmd": "echo 'Source vendored in monorepo — skipping upstream clone.'"},
            {"label": "Downloading model (~28GB — Mixtral-8x7B Q4)", "cmd": "cd {dir} && bash ./download_models.sh",
             "heartbeat": {"label": "pharmacy model", "path": "{dir}/models", "total_gb": 28}},
            # Register the downloaded GGUF with Ollama as 'medical-mixtral' (host-level;
            # the backend reads OLLAMA_MODEL=medical-mixtral from host Ollama). Idempotent:
            # skipped if 'ollama list' already shows it. cd {dir} so the Modelfile's
            # relative `FROM ./models/medical-ft-mixtral-q4` resolves.
            {"label": "Registering Ollama model (medical-mixtral)", "cmd": "ollama list | grep -q '^medical-mixtral' || (cd {dir} && ollama create medical-mixtral -f Modelfile.medical)"},
            {"label": "Building Docker image (~15 min — compiles llama.cpp CUDA sm_120)", "cmd": "cd {dir} && docker compose build"},
        ],
        "launch_cmd": "cd {dir} && bash ./start.sh -d",
        "port": 8000,
        "health_url": "http://localhost:8000/api/health",
        "teardown_strategy": {"type": "docker_compose"},
        "discovery": {"type": "docker_container", "patterns": ["pharmacy", "healthcare", "drug"]},
    },
    "pii": {
        "name": "PII Detection & Masking",
        "dir": "pii-demo-containerized-docker",
        "steps": [
            # Download both GGUFs via the in-repo helper (correct $HOME/demos path,
            # *.gguf only). Use the zgx env python (has huggingface_hub from
            # requirements.txt). snapshot_download is itself idempotent.
            {"label": "Downloading PII models (~22GB — TinyLlama + fine-tuned PII detector GGUFs)", "cmd": "cd {dir} && $HOME/miniforge3/envs/zgx/bin/python3 _dl_models.py",
             "heartbeat": {"label": "PII models", "path": "{dir}/models", "total_gb": 22}},
            # Register both with Ollama (host-level; backend reads BASE/FINETUNED model
            # names from host Ollama). Idempotent guards; cd {dir} so the Modelfiles'
            # relative `FROM ./models/*.gguf` resolve.
            {"label": "Registering Ollama model (tinyllama-pii)", "cmd": "ollama list | grep -q '^tinyllama-pii' || (cd {dir} && ollama create tinyllama-pii -f Modelfile.tinyllama-pii)"},
            {"label": "Registering Ollama model (pii-detector)", "cmd": "ollama list | grep -q '^pii-detector' || (cd {dir} && ollama create pii-detector -f Modelfile.pii-detector)"},
        ],
        "launch_cmd": "cd {dir} && docker compose up -d",
        "port": 8000,
        "port_path": "/app/",
        "health_url": "http://localhost:8000/",
        "teardown_strategy": {"type": "docker_compose"},
        "discovery": {"type": "docker_container", "patterns": ["pii"]},
    },
    "construction": {
        "name": "Construction Safety Assistant",
        "dir": "AEC-construction-safety",
        "steps": [
            {"label": "Source vendored — no clone needed", "cmd": "echo 'Source vendored in monorepo — skipping upstream clone.'"},
            {"label": "Installing Python dependencies", "cmd": "cd {dir} && bash ./install.sh"},
        ],
        "launch_cmd": "bash $HOME/demos/AEC-construction-safety/start_demo_8091.sh",
        "port": 8091,
        "health_url": "http://localhost:8091/",
        "teardown_strategy": {"type": "port_kill"},
        "discovery": {"type": "port_probe"},
    },
    "translation": {
        "name": "Private Document Translation",
        "dir": "document-translation",
        "steps": [
            {"label": "Source vendored — no clone needed", "cmd": "echo 'Source vendored in monorepo — skipping upstream clone.'"},
            {"label": "Creating Python virtual environment", "cmd": "cd {dir} && python3 -m venv document-translate-env"},
            {"label": "Installing Python dependencies", "cmd": "cd {dir} && bash ./install.sh"},
            # Fix 5: pre-fetch the translation model at INSTALL time so the demo has
            # NO demo-time internet dependency (the old behavior downloaded ~1.2GB on
            # the first 'Load Models' click — bad on a locked-down CWC network). The
            # backend (backend/main.py) loads facebook/nllb-200-distilled-600M via
            # transformers' from_pretrained() with NO cache_dir and the launcher sets
            # no HF_HOME, so it reads the DEFAULT HuggingFace cache
            # (~/.cache/huggingface/hub). We pre-fetch with the DEMO'S OWN venv python
            # (same huggingface_hub + same default cache resolution as the backend), so
            # the bytes land exactly where 'Load Models' later looks. snapshot_download
            # is idempotent — a re-run is a no-op once cached.
            {"label": "Pre-fetching translation model (~1.2GB — facebook/nllb-200-distilled-600M)",
             "cmd": "cd {dir} && ./document-translate-env/bin/python -c \"from huggingface_hub import snapshot_download; snapshot_download('facebook/nllb-200-distilled-600M')\"",
             "heartbeat": {"label": "translation model", "path": "~/.cache/huggingface/hub/models--facebook--nllb-200-distilled-600M", "total_gb": 1.2}},
        ],
        "launch_cmd": "bash $HOME/demos/document-translation/start_demo_8092.sh",
        "port": 8092,
        "note": "Model (facebook/nllb-200-distilled-600M, ~1.2GB) is pre-fetched into the HuggingFace cache at install time; the UI 'Load Models' button loads it from disk (no download).",
        "health_url": "http://localhost:8092/",
        "teardown_strategy": {"type": "port_kill"},
        "discovery": {"type": "port_probe"},
    },
    "pipeline": {
        "name": "Pipeline Pulse — O&G AI Monitoring",
        "dir": "pipeline-pulse",
        # Native demo: runs under the zgx env python (see start_demo_8088.sh), so its
        # imports must be installed INTO that env. pipeline_pulse_v6.py imports httpx
        # (already a global zgx dep) + pynvml (GPU telemetry). Installed here so the
        # orchestrator/launcher provision them; --timeout/--retries ride out slow
        # aarch64 wheel fetches. Then verify the imports actually resolve in-env.
        "steps": [
            {"label": "Installing pipeline deps into zgx env (httpx, pynvml)", "cmd": "$HOME/miniforge3/envs/zgx/bin/python3 -m pip install --timeout 60 --retries 10 httpx pynvml"},
            {"label": "Verifying pipeline imports (httpx, pynvml)", "cmd": "$HOME/miniforge3/envs/zgx/bin/python3 -c 'import httpx, pynvml; print(\"pipeline imports OK\")'"},
        ],
        "launch_cmd": "bash $HOME/demos/pipeline-pulse/start_demo_8088.sh",
        "port": 8088,
        "health_url": None,
        # process_pattern (not port_kill): same architecture/load-race as AI Vision
        # — a single nohup python (pipeline_pulse_v6.py) that warms up llama3.1:70b
        # before binding :8088, so Exit-while-loading could orphan it. The name is
        # unique, so pkill-by-name is safe; port: 8088 stays as fallthrough.
        "teardown_strategy": {"type": "process_pattern", "patterns": ["pipeline_pulse_v6.py"]},
        "discovery": {"type": "port_probe"},
        "readiness_check": {
            "files": [
                "~/demos/pipeline-pulse/pipeline_pulse_v6.py",
                "~/demos/pipeline-pulse/pipeline_pulse_v6.html",
            ],
            "ollama_model": "llama3.1:70b",
            "path": "~/demos/pipeline-pulse",
        },
    },
    "vision": {
        "name": "AI Vision — Real-Time Object Detection",
        "dir": "ai-vision",
        # Native demo: runs under the zgx env python (see start_demo_8094.sh), so its
        # imports must be installed INTO that env. vision_engine.py imports cv2 +
        # numpy + pycuda + tensorrt; vision_hw.py uses pynvml. Pins match the clean-box
        # validated set; tensorrt-cu13 comes from NVIDIA's index. opencv is the HEADLESS
        # build only (no GUI/X deps). pycuda compiles from source on aarch64 — SLOW is
        # NORMAL, hence --timeout 60 --retries 10. The engine itself is built AFTER this
        # step (install.py Phase 4b) using THIS env's tensorrt so build==runtime TRT.
        "steps": [
            {"label": "Installing vision deps into zgx env (opencv-headless, numpy, pycuda, tensorrt — pycuda compiles from source on aarch64; slow is normal)", "cmd": "$HOME/miniforge3/envs/zgx/bin/python3 -m pip install --timeout 60 --retries 10 --extra-index-url https://pypi.nvidia.com opencv-python-headless==4.13.0.92 numpy==2.4.6 pycuda==2026.1 tensorrt-cu13==10.15.1.29 pynvml"},
            {"label": "Verifying vision imports (cv2, numpy, pycuda, tensorrt, pynvml)", "cmd": "$HOME/miniforge3/envs/zgx/bin/python3 -c 'import cv2, numpy, pycuda.driver, tensorrt, pynvml; print(\"vision imports OK — cv2\", cv2.__version__, \"| numpy\", numpy.__version__, \"| tensorrt\", tensorrt.__version__)'"},
        ],
        "launch_cmd": "bash $HOME/demos/ai-vision/start_demo_8094.sh",
        "port": 8094,
        "health_url": None,
        # process_pattern (not port_kill): the backend loads a TRT engine + 70B
        # model for ~tens of seconds before it binds :8094. A port-kill can't hit a
        # process that hasn't bound its port yet, so Exit-while-loading orphaned the
        # backend (held 1.4 GiB GPU). pkill-by-name catches it regardless of bind
        # state; the declared port: 8094 is still added as a fallthrough by both
        # teardown paths, so this is belt-and-suspenders.
        "teardown_strategy": {"type": "process_pattern", "patterns": ["vision_demo.py", "vision_frontend.py"]},
        "discovery": {"type": "port_probe"},
        "readiness_check": {
            "files": [
                "~/yolov8s.trt",
                "~/zgx_videos/video1.mp4",
                "~/demos/ai-vision/vision_demo.py",
            ],
            "ollama_model": "llama3.1:70b",
            "path": "~/demos/ai-vision",
        },
    },
}
