from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams, MCPToolset
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

root_agent = Agent(
    model='gemini-2.5-flash',
    name='maps_Agent',
    description='A helpful assistant for user interact with google maps',
    instruction="""
    You are a helpful assistant. Your role is to assist users with questions related to locations and places using Google Maps.
    Your capabilities include:
    - Getting the coordinates of a place based on its name or address.
    - Retrieving detailed information about places using Google Maps tools.

    Tools:
    - get_place_location: Use this tool to obtain the latitude and longitude of a specified place.
    - get_place_details: Use this tool to fetch detailed information about a place using its coordinates, including 
    general information, reviews, and nearby points of interest.
    """,
    tools = [MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="http://127.0.0.1:8080/mcp"  # Local MCP server endpoint
        )
    )],

)