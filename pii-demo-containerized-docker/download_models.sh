#!/usr/bin/env bash
# Download both PII GGUFs into this demo's models/ directory.
# The install step then registers them with Ollama as 'tinyllama-pii' and
# 'pii-detector'.
#
# Self-locating (no hardcoded home-dir assumption). Delegates to _dl_models.py — the
# single source of truth for which GGUFs to fetch (*.gguf only) — so this script
# and the orchestrator's install step download exactly the same files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer the zgx env python (has huggingface_hub); fall back to PATH python3.
PY="$HOME/miniforge3/envs/zgx/bin/python3"
[ -x "$PY" ] || PY="python3"

echo "================================================"
echo "PII Models Download Script"
echo "================================================"
echo "TinyLlama (~2GB) + Fine-tuned PII Detector (~20GB)..."

"$PY" "$SCRIPT_DIR/_dl_models.py"

echo ""
echo "✅ Models downloaded to $SCRIPT_DIR/models/"
echo "   The installer will register them with Ollama (tinyllama-pii, pii-detector)."
