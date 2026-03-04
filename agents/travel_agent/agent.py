from __future__ import annotations

import asyncio

from deepagents import create_deep_agent
from dotenv import load_dotenv, find_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(find_dotenv())



# ---------------------------------------------------
# Agent wrapper class (direct prompt → agent; no parsing tools)
# ---------------------------------------------------

class TravelInsightsAgent:
    """
    DeepAgent (DeepAgents API + LangGraph) using Gemini.

    IMPORTANT:
    - We do NOT parse or extract fields with regex/tools.
    - We pass the user's prompt directly to the agent.
    - The agent asks for missing info (location and weather) in plain language.
    - Only when both are present does it output JSON matching TravelInsights.

    Input contract (in ONE prompt):
      - Location: (place name) and optionally "lat, lon"
      - Weather: short summary for the travel window
      - Optional: trip_days, preferences
    """

    SYSTEM_PROMPT = f"""
You are a place-specific travel insights agent.

SCOPE (STRICT):
- Only provide information about traveling to the place the user provides in their prompt.
- Do NOT browse the web.
- Do NOT geocode.
- Do NOT fetch weather.
- Do NOT invent coordinates or weather.

INPUT REQUIREMENTS (must be present in the user's prompt):
1) Location: either a place name OR latitude+longitude (both is ok).
2) Weather: a short weather summary for the trip window.

BEHAVIOR:
- If Location is missing, ask the user to provide it. DONT expect the weather to be very details, use whatever you can and have access to in the context.
- If Weather is missing, ask the user to provide it.
- If either is missing, STOP (do not produce the travel plan).

OUTPUT:
- If requirements are met: Return the travel insights in Markdown format that includes the following sections:
  1) Overview: A brief summary of the destination and what makes it unique.
  2) Stay & Neighborhoods: Recommendations on where to stay based on the provided location
        and preferences, including 5-8 neighborhood suggestions with brief rationales and tradeoffs.
 3) Itinerary Outline: A day-by-day outline of activities and sights to see, tailored to the provided weather summary and typical trip length.
    

- If requirements are NOT met: request the missing information in plain language, e.g. "Where are you planning to travel?" or "Can you provide a brief summary of the expected weather during your trip?"
"""

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.3,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.agent = None

    async def initialize(self):
        llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            # Uses GOOGLE_API_KEY from env by default (Gemini Developer API).
        )

        # No parsing tools. Prompt goes straight to the agent.
        self.agent = create_deep_agent(
            model=llm,
            tools=[],
            system_prompt=self.SYSTEM_PROMPT,
            # NOTE: We do NOT set response_format here because we want the agent
            # to be able to ask clarifying questions when location/weather missing.
            # When the requirements are met, it will output JSON matching the schema.
            name="TravelInsightsAgent",
        )
        return self

    async def answer_query(self, prompt: str) -> str:
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        if hasattr(self.agent, "ainvoke"):
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )
        else:
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )

        return result["messages"][-1].content


# ---------------------------------------------------
# Main (try it)
# ---------------------------------------------------

async def main():
    """
    Run:
      pip install deepagents langgraph langchain-google-genai pydantic
      export GOOGLE_API_KEY="..."
      python travel_deep_agent_place_only.py
    """
    agent = await TravelInsightsAgent().initialize()

    tests = [
        # Missing both -> should ask for location + weather
        "Help me plan a trip for 3 days. I like walkable cities and coffee.",
        # Missing weather -> should ask for weather
        "Plan a 4-day trip to Kyoto, Japan. Interests: temples, gardens. Budget: mid.",
        # Has both -> should output JSON TravelInsights
        "Plan a 3-day trip.\n"
        "Location: Barcelona, Spain (lat 41.3874, lon 2.1686)\n"
        "Weather: Warm sunny days ~26C with a light sea breeze; low chance of rain.\n"
        "Preferences: mid-budget, walkable, local food, museums.",
    ]

    for i, t in enumerate(tests, 1):
        print(f"\n================= TEST {i} =================")
        print("PROMPT:\n", t)
        resp = await agent.answer_query(t)
        print("\nRESPONSE:\n", resp)


if __name__ == "__main__":
    asyncio.run(main())