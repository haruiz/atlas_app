from typing import Optional, Dict, Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import Agent
from google.adk.models import LlmResponse, LlmRequest
from google.adk.tools import BaseTool, ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


from .tools import get_weather, get_place_location, get_place_details

agent_instructions = """
You are a helpful assistant designed to answer user questions and provide useful information, 
including weather updates and place details using Google Maps data.

Behavior Guidelines:
- If the user greets you, respond specifically with "Hello".
- If the user greets you without making any request, reply with "Hello" and ask, "How can I assist you?"
- If the user asks a direct question, provide the most accurate and helpful answer possible.

Tool Usage:
- get_weather: Retrieve the current weather information for a specified location.
- get_place_location: Obtain the precise latitude and longitude of a specified place.
- get_place_details: Fetch detailed information about a place using its geographic coordinates.

Always choose the most appropriate tool to fulfill the user's request, and respond clearly and concisely.
"""

def before_model(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Logs entry and checks 'skip_llm_agent' in session state.
    If True, returns Content to skip the agent's execution.
    If False or not present, returns None to allow execution.
    """
    agent_name = callback_context.agent_name
    print(f"[Callback] Before model call for agent: {agent_name}")

    # Inspect the last user message in the request contents
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    print(f"[Callback] Inspecting last user message: '{last_user_message}'")

    # check the context
    model_tools = llm_request.config.tools
    print(f"[Callback] Tools available to the model: {model_tools}")

    return None


def before_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """Inspects/modifies tool args or skips the tool call."""
    agent_name = tool_context.agent_name
    tool_name = tool.name
    print(f"[Callback] Before tool call for tool '{tool_name}' in agent '{agent_name}'")
    print(f"[Callback] Original args: {args}")
    return None


root_agent = Agent(
    name="assistant",                    # Internal agent name
    model="gemini-2.5-flash",            # LLM model to use
    instruction=agent_instructions,
    before_model_callback=before_model,
    before_tool_callback=before_tool,
    tools=[
        # Provides persistent memory during the session (non-long-term)
        PreloadMemoryTool(),

        # Direct tool integration example
        get_weather,
        get_place_location,
        get_place_details,

    ]
)
