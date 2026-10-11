from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import uvicorn
from llama_cpp import Llama
import re
import time
import os
import gc

app = FastAPI(title="PII Masking Demo", version="2.0.0")

# Enable CORS for remote frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Model paths - configurable via environment variables
# Defaults work for Docker container; override for bare-metal installs
# ============================================================================
BASE_MODEL_PATH = os.environ.get(
    "BASE_MODEL_PATH",
    "/app/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
)
FINETUNED_MODEL_PATH = os.environ.get(
    "FINETUNED_MODEL_PATH",
    "/app/models/pii_detector_Q4_K_M.gguf"
)

# GPU configuration
N_GPU_LAYERS = int(os.environ.get("N_GPU_LAYERS", "-1"))  # -1 = all layers on GPU
N_CTX = int(os.environ.get("N_CTX", "2048"))
N_BATCH = int(os.environ.get("N_BATCH", "4096"))
N_THREADS = int(os.environ.get("N_THREADS", "8"))

# Global variables for models
base_model = None
finetuned_model = None
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


def load_models():
    """Load both GGUF models into memory"""
    global base_model, finetuned_model, models_loaded

    try:
        print("Loading GGUF models...")

        # Check if model files exist
        if not os.path.exists(BASE_MODEL_PATH):
            print(f"❌ Base model (TinyLlama) not found at {BASE_MODEL_PATH}")
            print("   Make sure models are mounted at /app/models/")
            return False
        if not os.path.exists(FINETUNED_MODEL_PATH):
            print(f"❌ Finetuned model not found at {FINETUNED_MODEL_PATH}")
            print("   Make sure models are mounted at /app/models/")
            return False

        print(f"Loading TinyLlama base model from {BASE_MODEL_PATH}...")
        base_model = Llama(
            model_path=BASE_MODEL_PATH,
            n_gpu_layers=N_GPU_LAYERS,
            n_ctx=N_CTX,
            n_batch=N_BATCH,
            n_threads=N_THREADS,
            flash_attn=True,
            verbose=False
        )
        print("✅ TinyLlama loaded!")

        print(f"Loading finetuned Qwen2.5-32B model from {FINETUNED_MODEL_PATH}...")
        finetuned_model = Llama(
            model_path=FINETUNED_MODEL_PATH,
            n_gpu_layers=N_GPU_LAYERS,
            n_ctx=N_CTX,
            n_batch=N_BATCH,
            n_threads=N_THREADS,
            flash_attn=True,
            verbose=False
        )
        print("✅ Finetuned model loaded!")

        models_loaded = True
        return True

    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return False


def create_pii_prompt(text: str, is_finetuned: bool = False) -> str:
    """Create appropriate prompt for PII masking task"""
    if is_finetuned:
        prompt = f"<|im_start|>system\nMask all PII and PHI in text.<|im_end|>\n<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n"
    else:
        prompt = f"<|system|>\nMask PII: [NAME], [SSN], [PHONE], [EMAIL], [ADDRESS], [DATE].</s>\n<|user|>\n{text}</s>\n<|assistant|>\n"
    return prompt


def generate_with_gguf(model, prompt: str, max_tokens: int = 1024,
                       temperature: float = 0.1, model_type: str = "tinyllama",
                       input_text: str = "") -> tuple:
    """Generate masked text using GGUF model"""
    start_time = time.time()

    # Dynamic max_tokens based on input length
    if input_text:
        estimated = int(len(input_text.split()) * 1.5) + 30
        max_tokens = min(max_tokens, max(estimated, 50))

    try:
        if model_type == "qwen":
            stop_tokens = ["<|im_end|>", "<|im_start|>"]
        else:
            stop_tokens = ["</s>", "<|user|>", "<|system|>"]

        if model_type == "tinyllama":
            response = model(
                prompt,
                max_tokens=max_tokens,
                temperature=0.3,
                top_p=0.9,
                top_k=40,
                stop=stop_tokens,
                echo=False,
                repeat_penalty=1.15
            )
        else:
            response = model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop_tokens,
                echo=False,
                repeat_penalty=1.1
            )

        output = response['choices'][0]['text'].strip()
        elapsed_time = time.time() - start_time
        return output, elapsed_time

    except Exception as e:
        print(f"Error during generation: {e}")
        elapsed_time = time.time() - start_time
        return f"Error: {str(e)}", elapsed_time


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def read_root():
    return {
        "status": "PII Masking Demo Running",
        "version": "2.0.0-docker",
        "models_loaded": models_loaded,
        "base_model": os.path.basename(BASE_MODEL_PATH) if models_loaded else "Not loaded",
        "finetuned_model": os.path.basename(FINETUNED_MODEL_PATH) if models_loaded else "Not loaded"
    }


@app.get("/load_models")
async def load_models_endpoint():
    """Endpoint to trigger model loading"""
    if models_loaded:
        return {"status": "Models already loaded"}

    success = load_models()
    if success:
        return {"status": "Models loaded successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to load models. Check that model files are in /app/models/")


@app.post("/mask_pii")
async def mask_pii(request: PIIRequest):
    """Process text through both models and return masked versions"""

    if not models_loaded:
        success = load_models()
        if not success:
            raise HTTPException(
                status_code=503,
                detail="Models not loaded. Please check model paths."
            )

    try:
        # Generate with TinyLlama base model
        base_prompt = create_pii_prompt(request.text, is_finetuned=False)
        print(f"DEBUG: Base prompt length: {len(base_prompt)} chars")
        base_output, base_time = generate_with_gguf(
            base_model,
            base_prompt,
            request.max_tokens,
            request.temperature,
            model_type="tinyllama",
            input_text=request.text
        )

        # Generate with finetuned Qwen model
        finetuned_prompt = create_pii_prompt(request.text, is_finetuned=True)
        print(f"DEBUG: FT prompt length: {len(finetuned_prompt)} chars")
        finetuned_output, finetuned_time = generate_with_gguf(
            finetuned_model,
            finetuned_prompt,
            request.max_tokens,
            request.temperature,
            model_type="qwen",
            input_text=request.text
        )

        return PIIResponse(
            original_text=request.text,
            base_model_output=base_output,
            finetuned_model_output=finetuned_output,
            base_model_time=round(base_time, 2),
            finetuned_model_time=round(finetuned_time, 2),
            timestamp=datetime.now().isoformat(),
            status="success"
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
        status="test"
    )


# ============================================================================
# Mount frontend static files (serves index.html at /app)
# This eliminates the need for a separate HTTP server
# ============================================================================
FRONTEND_DIR = os.environ.get("FRONTEND_DIR", "/app/frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    print("=" * 60)
    print("PII Masking Demo - Containerized v2.0")
    print("=" * 60)
    print(f"Base Model:      {BASE_MODEL_PATH}")
    print(f"Finetuned Model: {FINETUNED_MODEL_PATH}")
    print(f"GPU Layers:      {N_GPU_LAYERS}")
    print(f"Context Window:  {N_CTX}")
    print("=" * 60)

    # Auto-load models on startup
    AUTO_LOAD = os.environ.get("AUTO_LOAD_MODELS", "true").lower() == "true"
    if AUTO_LOAD:
        print("\nLoading models on startup...")
        success = load_models()
        if success:
            print("✅ Both models loaded successfully!")
        else:
            print("⚠️  Models not loaded - use /load_models endpoint or check paths")
    else:
        print("\nAuto-load disabled. Use /load_models endpoint to load models.")

    # Print clickable access URLs
    # Detect the host's IP from inside the container by reading the default gateway
    # (Docker's default gateway is always the host machine)
    host_ip = os.environ.get("HOST_IP", "").strip()
    if not host_ip:
        try:
            with open("/proc/net/route") as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[1] == "00000000":  # default route
                        # Gateway IP is in hex, little-endian
                        hex_ip = fields[2]
                        host_ip = ".".join(
                            str(int(hex_ip[i:i+2], 16))
                            for i in range(6, -1, -2)
                        )
                        break
        except Exception:
            host_ip = "localhost"

    print("\n" + "=" * 60)
    print("🚀 Demo is ready!")
    print("=" * 60)
    print(f"  Frontend:  http://{host_ip}:8000/app/")
    print(f"  API:       http://{host_ip}:8000/")
    print(f"  API Docs:  http://{host_ip}:8000/docs")
    print("=" * 60 + "\n")

    # Single server serves both API and frontend
    uvicorn.run(app, host="0.0.0.0", port=8000)