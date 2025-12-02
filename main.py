from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from fastapi import FastAPI

from agents.atlas_agent.agent import root_agent as atlas_root_agent


# -------------------------------------------------------------------
# Wrap the agent inside an ADKAgent middleware
# This provides sessions, user identity, in-memory services,
# and the unified ADK API that frontend UI components expect.
# -------------------------------------------------------------------
ag_atlas_agent = ADKAgent(
    adk_agent=atlas_root_agent,            # The core ADK agent
    app_name="atlas_app",                # App identifier
    user_id="demo_user",                # Mock user ID (replace in production)
    session_timeout_seconds=3600,       # Session expiration
    use_in_memory_services=True         # Enables in-memory RAG + storage
)

# Create the FastAPI application
app = FastAPI(title="ADK Middleware Atlas Chat")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# -------------------------------------------------------------------
# Register an ADK-compliant endpoint with FastAPI.
# This exposes the chat API at "/".
# Your frontend (Next.js + CopilotKit) will call this endpoint.
# -------------------------------------------------------------------
add_adk_fastapi_endpoint(app, ag_atlas_agent, path="/")

# -------------------------------------------------------------------
# Run the development server using Uvicorn
# Only executes when running `python main.py`
# -------------------------------------------------------------------
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,        # Auto-reload on code changes
        workers=1           # Single worker recommended for MCP tools
    )