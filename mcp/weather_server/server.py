from typing import Any

from mcp.server.fastmcp import FastMCP

from tools import get_weather

# Create an MCP server
mcp = FastMCP("weather_server", port=8081, json_response=True)

@mcp.tool(name="get_weather", description="Get weather information for a given location.")
async def get_weather_tool(latitude: float, longitude: float) -> dict:
    """
    Get the weather for a given location.
    :param latitude: Latitude of the location.
    :param longitude: Longitude of the location.
    :return:
    """
    return await get_weather(latitude, longitude)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

