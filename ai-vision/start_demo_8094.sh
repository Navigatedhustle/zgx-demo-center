#!/bin/bash
# HP ZGX Nano — AI Vision Demo launcher
# Port: 8094

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$HOME/demos/logs"
mkdir -p "$LOG_DIR"

# Kill any existing instance on 8094
fuser -k 8094/tcp 2>/dev/null || true
pkill -f "vision_demo.py" 2>/dev/null || true
sleep 2

# Start AI Vision Demo
cd "$DEMO_DIR"
nohup $HOME/miniforge3/envs/zgx/bin/python3 vision_demo.py \
    > "$LOG_DIR/vision_demo.log" 2>&1 &

echo "AI Vision Demo starting on http://$(hostname -I | awk '{print $1}'):8094"
echo "Log: $LOG_DIR/vision_demo.log"
