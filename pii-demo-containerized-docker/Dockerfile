# =============================================================================
# PII Masking Demo - Docker Container
# Optimized for HP ZGX Nano with NVIDIA GB10 Grace Blackwell Superchip
# =============================================================================

# --- Stage 1: Build llama-cpp-python with CUDA support ---
FROM nvidia/cuda:12.8.0-devel-ubuntu24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev python3-venv \
    build-essential cmake git \
    && rm -rf /var/lib/apt/lists/*

# Build llama-cpp-python with CUDA
ENV CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=120"
ENV FORCE_CMAKE=1

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements-docker.txt /tmp/requirements.txt

# ============================================================================
# FIX: llama-cpp-python's cmake build links llama-mtmd-cli with
#   -Wl,-rpath,<tmpdir>/build/bin
# The linker resolves libggml-cuda.so from bin/, sees it needs libcuda.so.1
# (DT_NEEDED), and searches ONLY the rpath dirs - not system paths.
# Since libcuda.so.1 isn't in the build's bin/ dir, linking fails.
#
# Solution: Use pip's --no-build-isolation with a custom build script that
# patches the source to skip building the CLI tools we don't need.
# OR simpler: just make the build tolerate the link failure by allowing
# undefined symbols in executables.
#
# Simplest fix: add --allow-shlib-undefined to the exe linker flags.
# This tells the linker to not error on undefined symbols that come from
# shared libraries (which is fine - libcuda.so.1 will be present at runtime).
# ============================================================================
ENV CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=120 -DCMAKE_EXE_LINKER_FLAGS=-Wl,--allow-shlib-undefined"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir llama-cpp-python && \
    pip install --no-cache-dir -r /tmp/requirements.txt


# --- Stage 2: Runtime image (smaller, no compiler toolchain) ---
FROM nvidia/cuda:12.8.0-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TOKENIZERS_PARALLELISM=false
ENV OMP_NUM_THREADS=4

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set up application directory
WORKDIR /app

# Copy application code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Models are mounted at runtime, not baked into the image
VOLUME /app/models

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["python3", "backend/main.py"]