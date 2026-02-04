from typing import Any

from mcp.server.fastmcp import FastMCP

from tools import get_place_location, get_place_details

# Create an MCP server
mcp = FastMCP("geoloc_server", port=8080, json_response=True)

@mcp.tool(name="get_place_location", description="Get coordinates from an address using Google Maps API.")
async def get_place_location_tool(place_name: str) -> dict[str, Any]:
    """
    Get coordinates from an address using Google Maps API.
    :param place_name:
    :return:
    """
    return get_place_location(place_name)

@mcp.tool(name="get_place_details", description="Get place details using Google Maps Tool in Gemini.")
async def get_place_details_tool(place_name: str, query_prompt: str) -> dict[str, Any]:
    """
    Get place details using Google Maps Tool in Gemini.
    :param query_prompt: User query prompt for place details
    :param  place_name: Name of the place to get details for
    :return:
    """
    return get_place_details(place_name, query_prompt)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

