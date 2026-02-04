import os
from typing import Any, Dict, Union

import googlemaps
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv(find_dotenv())

gmaps_client = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
genai_client = genai.Client(http_options=types.HttpOptions(api_version="v1"))


# ---------------------------------------------------------------------------
# Utility: Get Geolocation
# ---------------------------------------------------------------------------
def get_place_location(place_name: str) -> Dict[str, Union[str, Dict[str, float]]]:
    """
    Get geographic coordinates from Google Maps API given a place name.
    """
    try:
        geocode_result = gmaps_client.geocode(place_name)
        if not geocode_result:
            return {
                "status": "error",
                "message": f"Could not find coordinates for: {place_name}"
            }
        location = geocode_result[0]["geometry"]["location"]
        return {
            "status": "success",
            "result": {"latitude": location["lat"], "longitude": location["lng"]}
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Utility: Get Place Details using Gemini + Maps Tool
# ---------------------------------------------------------------------------
def get_place_details(place_name: str, query_prompt: str) -> Dict[str, str]:
    """
    Get place details using Gemini’s Google Maps Tool.
    """
    try:
        # Get coordinates first
        location_result = get_place_location(place_name)

        if location_result["status"] == "error":
            raise Exception(location_result["message"])

        coords = location_result["result"]
        latitude = coords["latitude"]
        longitude = coords["longitude"]

        # Call Gemini with Maps tool
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query_prompt,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        google_maps=types.GoogleMaps(enable_widget=False)
                    )
                ],
                tool_config=types.ToolConfig(
                    retrieval_config=types.RetrievalConfig(
                        lat_lng=types.LatLng(
                            latitude=latitude,
                            longitude=longitude,
                        ),
                        language_code="en_US",
                    )
                ),
            ),
        )

        return {
            "status": "success",
            "result": response.text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get place details: {str(e)}"
        }


if __name__ == '__main__':
    import asyncio

    place_name = "New York"
    place_loc = get_place_location(place_name)
    print(f"Place Location for {place_name}: {place_loc}")