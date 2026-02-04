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

# Cleanup function to stop all background processes on exit
cleanup() {
  echo ""
  echo "Shutting down all services..."
  # Kill all background jobs started by this script
  kill $(jobs -p) 2>/dev/null
  exit
}

trap cleanup SIGINT SIGTERM EXIT

# Get the absolute path of the project root
PROJECT_ROOT=$(pwd)

echo "--- Starting Atlas Stack Sequentially ---"

# 1. Weather MCP Server (Port 8081)
echo "[1/6] Starting Weather MCP Server..."
(cd "$PROJECT_ROOT/mcp/weather_server" && uv run python server.py) &
wait_for_port 8081 "Weather MCP Server"

# 2. Maps MCP Server (Port 8080)
echo "[2/6] Starting Maps MCP Server..."
(cd "$PROJECT_ROOT/mcp/maps_server" && uv run python server.py) &
wait_for_port 8080 "Maps MCP Server"

# 3. Maps Agent (Port 8001)
echo "[3/6] Starting Maps Agent..."
(cd "$PROJECT_ROOT/agents/maps_agent" && uv run python a2a_server.py) &
wait_for_port 8001 "Maps Agent"

# 4. Weather Agent (Port 8002)
echo "[4/6] Starting Weather Agent..."
(cd "$PROJECT_ROOT/agents/weather_agent" && uv run python a2a_server.py) &
wait_for_port 8002 "Weather Agent"

# 5. Main Orchestrator (Port 8000)
echo "[5/6] Starting Main Orchestrator..."
(cd "$PROJECT_ROOT" && uv run python main.py) &
wait_for_port 8000 "Main Orchestrator"

# 6. UI (Foreground)
echo "[6/6] Starting UI..."
cd "$PROJECT_ROOT/ui" && yarn dev
