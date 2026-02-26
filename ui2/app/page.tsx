"use client";
import {useEffect, useState} from "react";
import {useFrontendTool, useRenderToolCall} from "@copilotkit/react-core";
import {CopilotChat} from "@copilotkit/react-ui";
import {useAgent} from "@copilotkitnext/react";

interface WeatherToolResult {
  temperature: number;
  conditions: string;
  humidity: number;
  windSpeed: number;
  feelsLike: number;
}


export default function Home() {
    const [background, setBackground] = useState<string>(
        "--copilot-kit-background-color"
    );
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

   useFrontendTool({
        name: "change_background",
        description: "Change the chat's background using any CSS background value (color, gradient, etc.).",
        parameters: [
            {
                name: "background",
                type: "string",
                description: "CSS background definition (colors, gradients, etc).",
            },
        ],
        // The tool handler executes when the LLM calls this tool.
        handler: ({background}) => {
            setBackground(background);
            return {
                status: "success",
                message: `Background changed to ${background}`,
            };
        },
    });

   useRenderToolCall({
        name: "get_place_location",
        description: "get the latitude and longitude of a place given its name.",
        available: "disabled",
        parameters: [{name: "place_name", type: "string", required: true}],
        render: ({args, status, result}) => {
            if (status === "inProgress") {
                return (
                    <div className="bg-[#667eea] text-white p-4 rounded-lg max-w-md">
                        <span className="animate-spin">⚙️ Retrieving location...</span>
                    </div>
                );
            }
            if (status === "complete" && result) {
                const {result: coords} = result;
                console.log("Place Location Result:", coords);
                return (
                    <div className="bg-[#667eea] text-white p-4 rounded-lg max-w-md">
                        📍 Location for {args.place_name}: {coords.latitude}, {coords.longitude}
                    </div>
                );
            }
            return null;
        }
    });

   useRenderToolCall({
        name: "get_weather",
        description: "Get the current weather for a specified location.",
        available: "disabled", // Using MCP or manually invoking elsewhere
        parameters: [{name: "location", type: "string", required: true}],
        render: ({args, status, result : toolResponse}) => {
            /* STATUS: inProgress --------------------------------------------------*/
            if (status === "inProgress") {
                return (
                    <div className="bg-[#667eea] text-white p-4 rounded-lg max-w-md">
                        <span className="animate-spin">⚙️ Retrieving weather...</span>
                    </div>
                );
            }

            /* STATUS: complete ----------------------------------------------------*/
            if (status === "complete" && toolResponse) {
                const weatherResult: WeatherToolResult | null = toolResponse?.result || null;
                console.log("Weather Result:", weatherResult);
                if (!weatherResult) {
                    return (
                        <div className="bg-red-300 text-red-900 p-4 rounded-lg max-w-md">
                            <strong>⚠️ Error:</strong> Unable to retrieve weather data. Please try again.
                        </div>
                    );
                }
                // Choose color based on weather conditions

                return (
                    <div className="rounded-xl mt-6 mb-4 max-w-md w-full">
                        {JSON.stringify(weatherResult)}
                    </div>
                );
            }

            return null;
        },
    });



  return (
    <main className="h-screen w-screen flex flex-row gap-4 p-4" style={{background}} >
        <div className="flex-1 h-full">
             <CopilotChat
                className="h-full rounded-2xl"
                onThumbsUp={() => setBackground("--copilot-kit-green-100")}
            />
            {events && (
                <div className="mt-4 p-2 bg-slate-50 rounded border max-h-48 overflow-y-auto">
                    <h3 className="text-sm font-bold mb-2">Event Stream:</h3>
                    {events.map((event, index) => (
                        <div key={index} className="text-xs text-gray-700 mb-1">
                            <pre>{JSON.stringify(event, null, 2)}</pre>
                        </div>
                    ))}
                </div>
            )}
        </div>
     </main>
  );
}
