#!/bin/bash

# Function to check if a port is open
wait_for_port() {
  local port=$1
  local name=$2
  echo "Waiting for $name to be ready on port $port..."
  while ! nc -z localhost $port; do
    sleep 0.5
  done
  echo "$name is ready!"
}

# Cleanup function to stop background processes on exit
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $(jobs -p) 2>/dev/null
  exit
}

trap cleanup SIGINT SIGTERM EXIT

PROJECT_ROOT=$(pwd)

echo "--- Starting Orchestrator and UI ---"

# 1. Main Orchestrator (Port 8000)
echo "[1/2] Starting Main Orchestrator..."
uv run python main.py &
wait_for_port 8000 "Main Orchestrator"

# 2. UI (Foreground)
echo "[2/2] Starting UI..."
cd "$PROJECT_ROOT/ui" && yarn dev
