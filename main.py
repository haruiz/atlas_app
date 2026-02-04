"""
Atlas Orchestrator Agent Service
--------------------------------

This module exposes the Orchestrator (Atlas) Agent as an HTTP endpoint using
FastAPI and the AG-UI Protocol. The orchestrator coordinates requests between
specialized A2A agents (such as the Weather and Maps agents) through Google's
Agent Development Kit (ADK).

Key Responsibilities:
- Wrap the LlmAgent with ADKAgent to provide session control, memory, and tool
  routing.
- Expose the orchestrator via the AG-UI Protocol so that UI components
  (chat widgets, tool UIs, etc.) can communicate seamlessly.
- Run a development server that hosts the orchestrator endpoint and integrates
  ADK's internal services.

This file is typically run as a standalone service for local development.
"""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables such as API keys or runtime configuration
load_dotenv()

# AG-UI and ADK integration utilities
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

# The orchestrator agent defined in the Atlas agent implementation
from agents.atlas_agent.agent import root_agent as orchestrator_agent


# ---------------------------------------------------------------------------
# ADKAgent Wrapper
# ---------------------------------------------------------------------------
# ADKAgent adapts an ADK LlmAgent so it can:
#   - Maintain user sessions
#   - Store in-memory conversational context
#   - Handle tool invocation through the ADK middleware
#   - Communicate using the AG-UI Protocol (used by front-end UI components)
# ---------------------------------------------------------------------------

adk_orchestrator_agent = ADKAgent(
    adk_agent=orchestrator_agent,
    app_name="orchestrator_app",      # Identifier for AG-UI front-end routing
    user_id="demo_user",              # Logical user identity for session tracking
    session_timeout_seconds=3600,     # Session expires after 1 hour of inactivity
    use_in_memory_services=True       # Enables in-memory state, tools, and memory
)


# ---------------------------------------------------------------------------
# FastAPI Application Setup
# ---------------------------------------------------------------------------
# The AG-UI Protocol is integrated as an HTTP endpoint via FastAPI. The
# orchestrator becomes available at the root path ("/"), enabling UI clients
# to send AG-UI structured requests and receive structured responses.
# ---------------------------------------------------------------------------

app = FastAPI(title="A2A Orchestrator Service (ADK + AG-UI Protocol)")

# Mount the orchestrator endpoint at `/`
add_adk_fastapi_endpoint(app, adk_orchestrator_agent, path="/")


# ---------------------------------------------------------------------------
# Development Server Entrypoint
# ---------------------------------------------------------------------------
# Uvicorn runs the FastAPI service locally. The configuration below is intended
# for development, with auto-reload enabled. ADK and MCP tools require running
# with a single worker to avoid shared-state inconsistencies.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,     # Auto-reloads the service upon code changes
        workers=1        # ADK/MCP systems require single-worker execution
    )
