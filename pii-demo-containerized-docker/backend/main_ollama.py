from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import httpx
import re
import time
import os

app = FastAPI(title="PII Masking Demo (Ollama)", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
BASE_MODEL_NAME = os.environ.get("BASE_MODEL_NAME", "tinyllama-pii")
FINETUNED_MODEL_NAME = os.environ.get("FINETUNED_MODEL_NAME", "pii-detector")
PII_PORT = int(os.environ.get("PII_PORT", "8000"))

models_loaded = False


class PIIRequest(BaseModel):
    text: str
    max_tokens: int = 256
    temperature: float = 0.1


class PIIResponse(BaseModel):
    original_text: str
    base_model_output: str
    finetuned_model_output: str
    base_model_time: float
    finetuned_model_time: float
    timestamp: str
    status: str


async def _list_ollama_models() -> list:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{OLLAMA_URL}/api/tags")
        r.raise_for_status()
        data = r.json()
        return [m.get("name", "") for m in data.get("models", [])]


def _model_present(available: list, name: str) -> bool:
    if name in available:
        return True
    return any(m.split(":")[0] == name for m in available)


async def _warm_model(model: str):
    payload = {
        "model": model,
        "prompt": "ok",
        "stream": False,
        "keep_alive": -1,
        "options": {"num_predict": 1},
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
    except Exception as e:
        print(f"⚠️  Warmup failed for {model}: {e}")


async def load_models() -> bool:
    """Verify both models exist in Ollama and warm them."""
    global models_loaded

    try:
        print(f"Checking Ollama at {OLLAMA_URL}...")
        available = await _list_ollama_models()
        print(f"Available Ollama models: {available}")

        if not _model_present(available, BASE_MODEL_NAME):
            print(f"❌ Base model '{BASE_MODEL_NAME}' not found in Ollama")
            return False
        if not _model_present(available, FINETUNED_MODEL_NAME):
            print(f"❌ Finetuned model '{FINETUNED_MODEL_NAME}' not found in Ollama")
            return False

        print(f"Warming {BASE_MODEL_NAME}...")
        await _warm_model(BASE_MODEL_NAME)
        print(f"✅ {BASE_MODEL_NAME} warm")

        print(f"Warming {FINETUNED_MODEL_NAME}...")
        await _warm_model(FINETUNED_MODEL_NAME)
        print(f"✅ {FINETUNED_MODEL_NAME} warm")

        models_loaded = True
        return True

    except Exception as e:
        print(f"❌ Error verifying models: {e}")
        return False


def create_pii_prompt(text: str, is_finetuned: bool = False) -> str:
    if is_finetuned:
        prompt = f"<|im_start|>system\nMask all PII and PHI in text.<|im_end|>\n<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n"
    else:
        prompt = f"<|system|>\nMask PII: [NAME], [SSN], [PHONE], [EMAIL], [ADDRESS], [DATE].</s>\n<|user|>\n{text}</s>\n<|assistant|>\n"
    return prompt


async def generate_with_ollama(model: str, prompt: str, max_tokens: int,
                               temperature: float, model_type: str,
                               input_text: str) -> tuple:
    start_time = time.time()

    if input_text:
        estimated = int(len(input_text.split()) * 1.5) + 30
        max_tokens = min(max_tokens, max(estimated, 50))

    if model_type == "qwen":
        stop_tokens = ["<|im_end|>", "<|im_start|>"]
        temp = temperature
        repeat_penalty = 1.1
        top_p = 0.9
        top_k = 40
    else:
        stop_tokens = ["</s>", "<|user|>", "<|system|>"]
        temp = 0.3
        repeat_penalty = 1.15
        top_p = 0.9
        top_k = 40

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": -1,
        "raw": True,
        "options": {
            "num_predict": max_tokens,
            "temperature": temp,
            "top_p": top_p,
            "top_k": top_k,
            "repeat_penalty": repeat_penalty,
            "stop": stop_tokens,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
        output = (data.get("response") or "").strip()
        elapsed_time = time.time() - start_time
        return output, elapsed_time

    except Exception as e:
        print(f"Error during generation ({model}): {e}")
        elapsed_time = time.time() - start_time
        return f"Error: {str(e)}", elapsed_time


@app.get("/")
def read_root():
    return {
        "status": "PII Masking Demo Running",
        "version": "3.0.0-ollama",
        "models_loaded": models_loaded,
        "base_model": BASE_MODEL_NAME,
        "finetuned_model": FINETUNED_MODEL_NAME,
        "ollama_url": OLLAMA_URL,
    }


@app.get("/load_models")
async def load_models_endpoint():
    if models_loaded:
        return {"status": "Models already loaded"}

    success = await load_models()
    if success:
        return {"status": "Models loaded successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify models in Ollama at {OLLAMA_URL}. "
                   f"Required: '{BASE_MODEL_NAME}', '{FINETUNED_MODEL_NAME}'."
        )


@app.post("/mask_pii")
async def mask_pii(request: PIIRequest):
    global models_loaded

    if not models_loaded:
        success = await load_models()
        if not success:
            raise HTTPException(
                status_code=503,
                detail="Models not loaded. Check Ollama is running and models exist."
            )

    try:
        base_prompt = create_pii_prompt(request.text, is_finetuned=False)
        print(f"DEBUG: Base prompt length: {len(base_prompt)} chars")
        base_output, base_time = await generate_with_ollama(
            BASE_MODEL_NAME,
            base_prompt,
            request.max_tokens,
            request.temperature,
            model_type="tinyllama",
            input_text=request.text,
        )

        finetuned_prompt = create_pii_prompt(request.text, is_finetuned=True)
        print(f"DEBUG: FT prompt length: {len(finetuned_prompt)} chars")
        finetuned_output, finetuned_time = await generate_with_ollama(
            FINETUNED_MODEL_NAME,
            finetuned_prompt,
            request.max_tokens,
            request.temperature,
            model_type="qwen",
            input_text=request.text,
        )

        return PIIResponse(
            original_text=request.text,
            base_model_output=base_output,
            finetuned_model_output=finetuned_output,
            base_model_time=round(base_time, 2),
            finetuned_model_time=round(finetuned_time, 2),
            timestamp=datetime.now().isoformat(),
            status="success",
        )

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test_offline")
async def test_offline(request: PIIRequest):
    """Test endpoint without models - uses regex-based masking"""
    text = request.text
    output = text
    output = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', output)
    output = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', output)
    output = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL]', output)
    output = re.sub(r'\b\d{5}\b', '[ZIP]', output)

    return PIIResponse(
        original_text=text,
        base_model_output=output,
        finetuned_model_output=output,
        base_model_time=0.1,
        finetuned_model_time=0.1,
        timestamp=datetime.now().isoformat(),
        status="test",
    )


FRONTEND_DIR = os.environ.get("FRONTEND_DIR", "/app/frontend")
if not os.path.isdir(FRONTEND_DIR):
    _local_frontend = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
    _local_frontend = os.path.normpath(_local_frontend)
    if os.path.isdir(_local_frontend):
        FRONTEND_DIR = _local_frontend

if os.path.isdir(FRONTEND_DIR):
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.on_event("startup")
async def startup_event():
    auto = os.environ.get("AUTO_LOAD_MODELS", "true").lower() == "true"
    if auto:
        print("\nVerifying models on startup...")
        ok = await load_models()
        if ok:
            print("✅ Both models verified and warm!")
        else:
            print("⚠️  Models not verified — use /load_models endpoint")
    else:
        print("\nAuto-load disabled. Use /load_models endpoint.")


if __name__ == "__main__":
    print("=" * 60)
    print("PII Masking Demo - Ollama backend v3.0")
    print("=" * 60)
    print(f"Ollama URL:       {OLLAMA_URL}")
    print(f"Base Model:       {BASE_MODEL_NAME}")
    print(f"Finetuned Model:  {FINETUNED_MODEL_NAME}")
    print(f"Port:             {PII_PORT}")
    print("=" * 60)

    host_ip = os.environ.get("HOST_IP", "").strip() or "localhost"
    print("\n" + "=" * 60)
    print("🚀 Demo is ready!")
    print("=" * 60)
    print(f"  Frontend:  http://{host_ip}:{PII_PORT}/app/")
    print(f"  API:       http://{host_ip}:{PII_PORT}/")
    print(f"  API Docs:  http://{host_ip}:{PII_PORT}/docs")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=PII_PORT)
