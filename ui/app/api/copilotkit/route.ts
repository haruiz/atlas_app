import { A2AMiddlewareAgent } from "@ag-ui/a2a-middleware"
import {CopilotRuntime, copilotRuntimeNextJSAppRouterEndpoint, ExperimentalEmptyAdapter} from "@copilotkit/runtime";
import {AbstractAgent, HttpAgent} from "@ag-ui/client";
import {NextRequest} from "next/server";



export async function POST(request: NextRequest) {
// These first two are the urls to the a2a agents
const weatherAgentUrl = process.env.WEATHER_AGENT_URL || "http://localhost:8002";
const mapsAgentUrl = process.env.MAPS_AGENT_URL || "http://localhost:8001";
const orchestratorUrl = process.env.ORCHESTRATOR_URL || "http://localhost:8000";
const travelInsightsAgentUrl = process.env.TRAVEL_INSIGHTS_AGENT_URL || "http://localhost:8003";

// the orchestrator agent we pass to the middleware needs to be an instance of a derivative of an ag-ui `AbstractAgent`
// In this case, we have access to the agent via url, so we can gain an instance using the `HttpAgent` class
const orchestrationAgent: AbstractAgent = new HttpAgent({
  url: orchestratorUrl,
});

// A2A Middleware: Wraps orchestrator and injects send_message_to_a2a_agent tool
// This allows orchestrator to communicate with A2A agents transparently
const a2aMiddlewareAgent = new A2AMiddlewareAgent({
  description:
    "An orchestrator agent that coordinates two specialized agents: Weather Agent and Maps Agent build on the ADK framework.",
  // We pass the urls to the a2a agents, the middleware will handle the connections
  agentUrls: [
    weatherAgentUrl,
    mapsAgentUrl,
    travelInsightsAgentUrl
  ],
  // Pass the agent instance
  orchestrationAgent
});

// CopilotKit runtime connects frontend to agent system
  // CopilotKit runtime connects frontend to agent system
  const runtime = new CopilotRuntime({
    agents: {
      a2a_chat: a2aMiddlewareAgent, // Must match agent prop in <CopilotKit agent="a2a_chat">
    },
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(request);
}
