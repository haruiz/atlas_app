import httpx
from typing import Dict, Any, Optional


# ---------------------------------------------------------------------------
# Weather Code Mapping (constant)
# ---------------------------------------------------------------------------
WEATHER_CODE_MAP: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    95: "Thunderstorm",
    99: "Thunderstorm with hail",
}


def get_weather_condition(code: Optional[int]) -> str:
    """
    Convert a weather code into a human-readable description.

    Args:
        code: Weather condition code.

    Returns:
        A descriptive string representing the weather condition.
    """
    return WEATHER_CODE_MAP.get(code, "Unknown")


# ---------------------------------------------------------------------------
# Weather Fetching
# ---------------------------------------------------------------------------
async def get_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Fetch current weather conditions for a given latitude and longitude.

    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.

    Returns:
        A dictionary containing:
            - status: "success" or "error"
            - result: weather fields (if success)
            - message: error message (if error)
    """
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
        "wind_speed_10m,wind_gusts_10m,weather_code"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            current = data.get("current")

            if not current:
                return {"status": "error", "message": "Weather API returned no 'current' data."}

            result = {
                "temperature": current.get("temperature_2m"),
                "feelsLike": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "windSpeed": current.get("wind_speed_10m"),
                "windGust": current.get("wind_gusts_10m"),
                "conditions": get_weather_condition(current.get("weather_code")),
            }

            return {"status": "success", "result": result}

    except httpx.HTTPError as e:
        return {"status": "error", "message": f"HTTP error: {str(e)}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Example Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio

    # Example: New York City coordinates
    nyc_lat, nyc_lon = 40.7128, -74.0060

    weather = asyncio.run(get_weather(nyc_lat, nyc_lon))
    print("Weather:", weather)
