from typing import Optional, Dict, Any

from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool, ToolContext, AgentTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())


# ======================================================================
# CALLBACKS
# ======================================================================

def before_model(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """
    Executes before the model handles a request.
    Allows inspection of inputs, debugging, or intercepting execution.

    Return:
        - LlmResponse to skip model execution
        - None to allow normal execution
    """
    agent_name = callback_context.agent_name
    print(f"[Orchestrator Callback] before_model for agent: {agent_name}")

    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == "user":
        parts = llm_request.contents[-1].parts
        if parts:
            last_user_message = parts[0].text

    print(f"[Orchestrator Callback] User message: {last_user_message}")

    print("[Orchestrator Callback] Tools available to model:")
    for tool in llm_request.config.tools or []:
        print(f"  - {tool.name}")

    return None


def before_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    Executes before any tool call.
    Allows modification of arguments or skipping execution.
    """
    print(
        f"[Orchestrator Callback] before_tool: '{tool.name}' "
        f"(agent: {tool_context.agent_name})"
    )
    print(f"[Orchestrator Callback] Tool arguments: {args}")
    return None


# ======================================================================
# REMOTE AGENTS (enable when servers are available to test a2a locally)
# ======================================================================
# maps_agent = RemoteA2aAgent(
#     name="maps_agent",
#     description="Provides geocoding, place lookup, and mapping utilities.",
#     agent_card=f"http://127.0.0.1:8001{AGENT_CARD_WELL_KNOWN_PATH}",
# )
#
# weather_agent = RemoteA2aAgent(
#     name="weather_agent",
#     description="Retrieves real-time weather conditions for a given coordinate.",
#     agent_card=f"http://127.0.0.1:8002{AGENT_CARD_WELL_KNOWN_PATH}",
# )


# ======================================================================
# ORCHESTRATOR AGENT
# ======================================================================

root_agent = Agent(
    name="OrchestratorAgent",
    model="gemini-2.5-pro",

    # Uncomment for debugging
    # before_tool_callback=before_tool,
    # before_model_callback=before_model,

    tools=[
        PreloadMemoryTool(),

        # When remote agents are active:
        # AgentTool(agent=maps_agent),
        # AgentTool(agent=weather_agent),
    ],

    instruction="""
    You are the Orchestrator Agent. Your role is to coordinate two specialized agents:
    
    - maps_agent: Resolves place names, coordinates, and map-related queries.
    - weather_agent: Retrieves weather information using geographic coordinates.
    
    Your responsibility is to determine when each agent should be called, how their outputs should be used, and how to produce a final integrated response for the user.
    
    ----------------------------------------------------------------------
    Workflow for Weather Queries
    ----------------------------------------------------------------------
    
    When the user requests weather information for a location:
    
    1. Call maps_agent  
       Input: the place name or location text.  
       Output: latitude and longitude.
    
    2. Call weather_agent  
       Input: coordinates returned by maps_agent.  
       Output: structured weather information.
    
    3. Combine both results into a clear, user-facing response.
    
    ----------------------------------------------------------------------
    Workflow for Location or Mapping Queries
    ----------------------------------------------------------------------
    
    If the user asks only for location information, directions, or coordinates:
    
    1. Call maps_agent directly.  
    2. Return the result to the user.
    
    ----------------------------------------------------------------------
    Execution Rules
    ----------------------------------------------------------------------
    
    - Execute agent calls in sequential order.  
    - Do not call multiple agents at the same time.  
    - Always wait for the response of the previous agent before making a new call.  
    - Pass intermediate outputs to the next agent when required.  
    - Do not fabricate or assume agent outputs; always rely on actual tool responses.  
    - Provide a final, coherent response after completing the workflow.
    
    ----------------------------------------------------------------------
    """,
)
