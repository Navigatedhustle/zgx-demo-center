#!/usr/bin/env bash
# Start the PII Masking demo (Ollama backend) on port 8000.
# Logs to ~/demos/logs/pii_demo.log

set -u

PORT="${PII_PORT:-8000}"
PY="${HOME}/miniforge3/envs/zgx/bin/python3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${SCRIPT_DIR}/backend/main_ollama.py"
LOG_DIR="${HOME}/demos/logs"
mkdir -p "${LOG_DIR}"
LOG="${LOG_DIR}/pii_demo.log"

echo "[start_pii_ollama] Killing any existing process on port ${PORT}..."
fuser -k "${PORT}/tcp" 2>/dev/null || true
pkill -f "main_ollama.py" 2>/dev/null || true
sleep 1

if [[ ! -x "${PY}" ]]; then
  echo "[start_pii_ollama] ERROR: zgx Python not found at ${PY}" >&2
  exit 1
fi

if [[ ! -f "${APP}" ]]; then
  echo "[start_pii_ollama] ERROR: app not found at ${APP}" >&2
  exit 1
fi

echo "[start_pii_ollama] Launching ${APP} on port ${PORT}..."
echo "[start_pii_ollama] Logs: ${LOG}"

cd "${SCRIPT_DIR}"
nohup env PII_PORT="${PORT}" "${PY}" "${APP}" > "${LOG}" 2>&1 &
PID=$!
disown 2>/dev/null || true

echo "[start_pii_ollama] Started PID ${PID}"
echo "[start_pii_ollama] Tail log:  tail -f ${LOG}"
echo "[start_pii_ollama] Frontend:  http://localhost:${PORT}/app/"
