from google.adk.agents.llm_agent import Agent
from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel
from google.adk.tools import MCPToolset
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams

load_dotenv(find_dotenv())

class WeatherData(BaseModel):
    temperature: float
    conditions: str
    humidity: float
    windSpeed: float
    feelsLike: float

root_agent = Agent(
    model='gemini-2.5-flash',
    name='weather_agent',
    description='A helpful assistant which provides users with weather information',
    instruction="""
    You are a Weather Agent. Your role is to assist users with any weather-related queries.
    Provide clear, accurate, and helpful weather information for any location the user requests.
    Always rely on the available tools to retrieve or generate weather data, and use them whenever
    necessary to answer user questions.
    """,
    output_schema=WeatherData,
    tools=[ MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="http://127.0.0.1:8081/mcp"   # Local MCP server endpoint
            )
        )],
)
