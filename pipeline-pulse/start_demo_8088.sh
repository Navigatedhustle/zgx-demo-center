#!/bin/bash
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$HOME/demos/logs"
mkdir -p "$LOG_DIR"
NANO_IP=$(hostname -I | awk '{print $1}')

# Kill any existing instance on 8088
fuser -k 8088/tcp 2>/dev/null || true
sleep 2

# Start Pipeline Pulse on port 8088
cd "$DEMO_DIR"
export PP_PORT=8088
nohup $HOME/miniforge3/envs/zgx/bin/python3 pipeline_pulse_v6.py > "$LOG_DIR/pipeline_pulse_demo.log" 2>&1 &

echo "Pipeline Pulse (Demo Center) starting on http://${NANO_IP}:8088"
