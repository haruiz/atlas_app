#!/bin/bash

# Ports used by the stack
PORTS=(8081 8080 8001 8002 8003 8000)

# Kill any process using a port
kill_port() {
  local port=$1
  pid=$(lsof -ti tcp:$port)

  if [ ! -z "$pid" ]; then
    echo "Killing process on port $port (PID $pid)"
    kill -9 $pid 2>/dev/null
  fi
}

# Kill all required ports before starting
cleanup_ports() {
  echo "Cleaning existing services on required ports..."
  for port in "${PORTS[@]}"; do
    kill_port $port
  done
}

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

# Cleanup function to stop background services
cleanup() {
  echo ""
  echo "Shutting down all services..."

  # Kill background jobs
  kill $(jobs -p) 2>/dev/null

  # Free ports again
  cleanup_ports

  exit
}

trap cleanup SIGINT SIGTERM EXIT

# Get project root
PROJECT_ROOT=$(pwd)

echo "--- Preparing Atlas Stack ---"

cleanup_ports

echo "--- Starting Atlas Stack Sequentially ---"

# 1. Weather MCP Server (Port 8081)
echo "[1/7] Starting Weather MCP Server..."
(cd "$PROJECT_ROOT/mcp/weather_server" && uv run python server.py) &
wait_for_port 8081 "Weather MCP Server"

# 2. Maps MCP Server (Port 8080)
echo "[2/7] Starting Maps MCP Server..."
(cd "$PROJECT_ROOT/mcp/maps_server" && uv run python server.py) &
wait_for_port 8080 "Maps MCP Server"

# 3. Maps Agent (Port 8001)
echo "[3/7] Starting Maps Agent..."
(cd "$PROJECT_ROOT/agents/maps_agent" && uv run python a2a_server.py) &
wait_for_port 8001 "Maps Agent"

# 4. Weather Agent (Port 8002)
echo "[4/7] Starting Weather Agent..."
(cd "$PROJECT_ROOT/agents/weather_agent" && uv run python a2a_server.py) &
wait_for_port 8002 "Weather Agent"

# 5. Travel Insights Agent (Port 8003)
echo "[5/7] Starting Travel Insights Agent..."
(cd "$PROJECT_ROOT/agents/travel_agent" && uv run python a2a_server.py) &
wait_for_port 8003 "Travel Insights Agent"

# 6. Main Orchestrator (Port 8000)
echo "[6/7] Starting Main Orchestrator..."
(cd "$PROJECT_ROOT" && uv run python main.py) &
wait_for_port 8000 "Main Orchestrator"

# 7. UI (Foreground)
echo "[7/7] Starting UI..."
cd "$PROJECT_ROOT/ui" && yarn dev