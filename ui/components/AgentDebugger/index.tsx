"use client";

import React, { useState, useEffect } from "react";
import { useAgent } from "@copilotkitnext/react";

function getTypeColor(type: string) {
  if (type.startsWith("TEXT_MESSAGE")) return "text-blue-600";
  if (type.startsWith("TOOL_CALL")) return "text-purple-600";
  if (type === "TOOL_RESULT") return "text-green-600";
  return "text-gray-600";
}


function GenericEventCard({ event }: { event: any }) {
  // Note: Data is accessed DIRECTLY on the event object. There is no 'payload' wrapper!
  const { type, agentId } = event;
  const timestamp = event.timestamp || event._receivedAt;

  // ... (styling logic omitted for brevity)

  return (
    <div className="border border-gray-200 rounded p-3 text-sm bg-white font-mono">
      {/* Event Header */}
      <div className="flex justify-between mb-2">
         <span className={`font-bold uppercase ${getTypeColor(type)}`}>{type}</span>
         <span className="text-xs text-gray-500">{agentId}</span>
      </div>

      <div className="text-xs text-gray-700 overflow-x-auto break-all">
        {/* Text Streaming */}
        {type === "TEXT_MESSAGE_CONTENT" && (
          <div><span className="font-bold text-blue-400">Delta: </span>"{event.delta}"</div>
        )}

        {/* Tool Args */}
        {type === "TOOL_CALL_ARGS" && (
          <div><span className="font-bold text-purple-600">Arg Delta: </span>{event.delta}</div>
        )}

        {/* Raw View */}
        <details className="mt-2 text-[10px] text-gray-400">
            <summary className="cursor-pointer">Raw Event</summary>
            <pre className="bg-slate-50 p-2 mt-1">{JSON.stringify(event, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}

export default function AgentDebugger() {
  const [events, setEvents] = useState<any[]>([]);

  const { agent } = useAgent({
    agentId: "atlas_agent"
  });

  useEffect(() => {
    if (agent) {
        const subscriber = {
            // Catch-all handler for the raw stream
            onEvent: ({ event }: { event: any }) => {
                // Enrich with local timestamp if missing
                const enrichedEvent = {
                    ...event,
                    _receivedAt: Date.now()
                };
                setEvents((prev) => [enrichedEvent, ...prev]);
            }
        };

        const subscription = agent.subscribe(subscriber);
        return () => subscription.unsubscribe();
    }
  }, [agent]);

  return (
      <div className="flex flex-col gap-2 h-96 overflow-y-auto bg-slate-50 p-4 rounded border">
        {events.map((event, idx) => (
          <GenericEventCard key={event.id || idx} event={event} />
        ))}
      </div>
  );
}
