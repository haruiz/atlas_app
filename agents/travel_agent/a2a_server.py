import os

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from dotenv import load_dotenv

from agent import TravelInsightsAgent


# ============================================================
# A2A Executor wrapper
# ============================================================

class TravelInsightsAgentExecutor(AgentExecutor):
    """A2A executor for the TravelInsightsAgent (Gemini + DeepAgents)."""

    def __init__(self) -> None:
        # Don't await in __init__
        self.agent = None

    async def _ensure_initialized(self) -> None:
        if self.agent is None:
            self.agent = await TravelInsightsAgent().initialize()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._ensure_initialized()

        prompt = context.get_user_input()
        response = await self.agent.answer_query(prompt)

        await event_queue.enqueue_event(new_agent_text_message(response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # No background tasks to cancel in this minimal version
        return


# ============================================================
# Server main
# ============================================================

def main():
    print("Running Travel Insights Agent (A2A + DeepAgents + Gemini)")
    load_dotenv()

    HOST = os.environ.get("AGENT_HOST", "localhost")
    PORT = int(os.environ.get("TRAVEL_AGENT_PORT", "8003"))

    skill = AgentSkill(
        id="travel_insights",
        name="Travel Insights (Place Only)",
        description=(
            "Provides travel insights ONLY about the place in the user's prompt. "
            "Requires the user to provide location and a weather summary in the same prompt; "
            "otherwise it asks for what's missing."
        ),
        tags=["travel", "itinerary", "logistics", "food", "budget"],
        examples=[
            "Plan a 3-day trip.\n"
            "Location: Kyoto, Japan (lat 35.0116, lon 135.7681)\n"
            "Weather: Mild days, cool evenings, occasional rain.\n"
            "Preferences: temples, gardens, coffee, vegetarian-friendly.",

            "I want travel tips. Location: Barcelona. Weather: Warm and sunny, light breeze. 4 days mid-budget.",
        ],
    )

    agent_card = AgentCard(
        name="TravelInsightsAgent",
        description="A place-specific travel insights agent powered by Gemini + DeepAgents (LangGraph).",
        url=f"http://{HOST}:{PORT}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=TravelInsightsAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()