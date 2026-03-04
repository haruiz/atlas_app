from __future__ import annotations

import json
import os
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, ValidationError

from deepagents import create_deep_agent
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


# -----------------------------
# Required user inputs
# -----------------------------

class Location(BaseModel):
    name: str = Field(..., description="Human-readable place name (city/region/country)")
    latitude: float
    longitude: float


class ProvidedWeather(BaseModel):
    summary: str = Field(..., description="Short weather summary for the travel window")
    daily: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Optional daily breakdown (date, tmin, tmax, precip, wind, etc.)",
    )
    units: Optional[str] = Field(default=None, description="metric/imperial or similar")


class TravelInputs(BaseModel):
    """
    Minimal payload required to produce place-specific travel insights.
    """
    location: Location
    weather: ProvidedWeather
    trip_days: int = Field(3, ge=1, le=30)
    preferences: Optional[dict[str, Any]] = Field(
        default=None,
        description="Interests, diet, budget, pace, mobility constraints, etc.",
    )


# -----------------------------
# Output schema: place-only insights
# -----------------------------

class TravelInsights(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    trip_days: int

    weather_summary: str

    # Place-specific guidance (no generic “travel anywhere” filler)
    best_areas_to_stay: list[str]
    what_to_do: list[str]
    local_food_to_try: list[str]
    getting_around: list[str]
    typical_costs_and_budget_tips: list[str]
    safety_and_practical_watchouts: list[str]

    # Make assumptions explicit; no external citations since we are not browsing
    assumptions: list[str] = Field(default_factory=list)


# -----------------------------
# Tool: validate inputs, return missing fields
# -----------------------------

def validate_travel_inputs(payload: dict) -> dict:
    """
    Validates presence of location + weather.
    If missing, returns missing fields so the agent asks for them.
    """
    try:
        parsed = TravelInputs.model_validate(payload)
        return {"ok": True, "inputs": parsed.model_dump()}
    except ValidationError as e:
        missing = []
        invalid = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err.get("loc", []))
            if err.get("type") == "missing":
                missing.append(loc)
            else:
                invalid.append({"field": loc, "issue": err.get("msg")})
        return {
            "ok": False,
            "error": "Missing or invalid travel inputs.",
            "missing_fields": sorted(set(missing)),
            "invalid_fields": invalid[:8],
        }


# -----------------------------
# System prompt: strict behavior
# -----------------------------

SYSTEM_PROMPT = """
You are a place-specific travel insights agent.

SCOPE (STRICT):
- Only provide information about traveling to the place the user provides.
- Do NOT geocode, do NOT fetch weather, do NOT browse the web.
- Assume the user WILL provide:
  (1) location: {name, latitude, longitude}
  (2) weather: {summary, daily?}
- If location or weather is missing/invalid, ask for exactly what is missing and STOP.

WORKFLOW:
1) Ask the user for a single JSON/dict payload if you don't have one.
2) Call validate_travel_inputs(payload).
3) If ok=false: ask for the missing/invalid fields in one concise message.
4) If ok=true: produce TravelInsights. Keep it practical and specific to that place.
5) Avoid generic filler; tie recommendations to the provided weather and typical trip-days.

OUTPUT:
- Must match the TravelInsights schema.
"""


# Optional subagents (no tools; they just help structure)
SUBAGENTS = [
    {
        "name": "stay_and_neighborhoods",
        "description": "Recommends areas to stay and how to choose based on preferences.",
        "system_prompt": "Recommend 5-8 areas/neighborhoods to stay with 1-line rationale each, plus tradeoffs.",
        "tools": [],
    },
    {
        "name": "itinerary_designer",
        "description": "Creates a tight trip plan aligned to weather and trip length.",
        "system_prompt": "Propose a day-by-day outline for the given trip_days, mindful of weather summary/daily notes.",
        "tools": [],
    },
]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
)

agent = create_deep_agent(
    model=llm,
    tools=[validate_travel_inputs],
    system_prompt=SYSTEM_PROMPT,
    subagents=SUBAGENTS,
    response_format=TravelInsights,
    name="travel_place_only_agent",
)



def main():

    print("\nTravel Deep Agent (Gemini)")
    print("Paste a JSON payload with location + weather\n")

    example = {
        "location": {
            "name": "Kyoto, Japan",
            "latitude": 35.0116,
            "longitude": 135.7681
        },
        "weather": {
            "summary": "Late April mild temperatures with occasional rain",
        },
        "trip_days": 4,
        "preferences": {
            "diet": "vegetarian",
            "interests": ["temples", "gardens", "coffee"],
            "budget": "mid"
        }
    }


    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": json.dumps(example, indent=2)
            }
        ]
    })

    print("\nAgent response:\n")

    try:
        content = result["messages"][-1].content

        if isinstance(content, dict):
            print(json.dumps(content, indent=2))
        else:
            print(content)

    except Exception as e:
        print(result)


# ---------------------------------------------------
# Entry point
# ---------------------------------------------------

if __name__ == "__main__":
    main()
