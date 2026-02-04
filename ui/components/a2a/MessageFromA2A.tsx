/**
 * Displays incoming A2A responses (Agent → Orchestrator).
 * Blue box with sender/receiver badges. Actual data renders separately in main UI.
 */

import React from "react";
import {getAgentStyle} from "./agent-styles";
import GoogleMap from "@/components/GoogleMap";
import WeatherCard, {getThemeColor, WeatherToolResult} from "@/components/WeatherCard";

type MessageActionRenderProps = {
    status: string;
    result?: object;
    args: {
        agentName?: string;
    };
};

export const MessageFromA2A: React.FC<MessageActionRenderProps> = ({result, status, args}) => {
    switch (status) {
        case "complete":
            break;
        default:
            return null;
    }

    if (!args.agentName) {
        return null;
    }

    const agentStyle = getAgentStyle(args.agentName);

    const history = result?.history || [];

    /** Extract all function calls */
    const functionCalls = history
        .flatMap(msg => msg.parts)
        .filter(
            part =>
                part.kind === "data" &&
                part.metadata?.adk_type === "function_call"
        )
        .map(part => part.data);

    /** Extract all function responses */
    const functionResponses = history
        .flatMap(msg => msg.parts)
        .filter(
            part =>
                part.kind === "data" &&
                part.metadata?.adk_type === "function_response"
        )
        .map(part => part.data);

    function getFunctionResponseComponent(
        functionName: string,
        functionResponse: any
    ) {
        const structuredResult = functionResponse?.structuredContent?.result;
        const contentBlock = functionResponse?.content?.[0];

        switch (functionName) {
            case "get_place_location": {
                const lat = structuredResult?.latitude;
                const lng = structuredResult?.longitude;

                if (!lat || !lng) return null;

                return (
                    <div className="flex items-center gap-2 mt-2">
                        <GoogleMap lat={lat} lng={lng}/>
                    </div>
                );
            }

            case "get_weather": {
                if (contentBlock?.type !== "text") return null;

                let parsed;
                try {
                    parsed = JSON.parse(contentBlock.text);
                } catch (err) {
                    console.error("Invalid JSON in get_weather response:", err);
                    return null;
                }

                const weather = parsed?.result;
                if (!weather) return null;

                const themeColor = getThemeColor(weather.conditions);

                const weatherData: WeatherToolResult = {
                    temperature: weather.temperature,
                    conditions: weather.conditions,
                    humidity: weather.humidity,
                    windSpeed: weather.windSpeed,
                    feelsLike: weather.feelsLike,
                };

                return (
                    <div className="flex items-center gap-2 mt-2">
                        <WeatherCard
                            themeColor={themeColor}
                            location={weather.location}
                            result={weatherData}
                            status="complete"
                        />
                    </div>
                );
            }

            default:
                return null;
        }
    }


    return (
        <div className="my-2">
            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 min-w-[200px] flex-shrink-0">
                        <div className="flex flex-col items-center">
              <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold border-2 ${agentStyle.bgColor} ${agentStyle.textColor} ${agentStyle.borderColor} flex items-center gap-1`}
              >
                <span>{agentStyle.icon}</span>
                <span>{args.agentName}</span>
              </span>
                            {agentStyle.framework && (
                                <span className="text-[9px] text-gray-500 mt-0.5">{agentStyle.framework}</span>
                            )}
                        </div>

                        <span className="text-gray-400 text-sm">→</span>

                        <div className="flex flex-col items-center">
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-700 text-white">
                Orchestrator
              </span>
                            <span className="text-[9px] text-gray-500 mt-0.5">ADK</span>
                        </div>
                    </div>

                    <span className="text-xs text-gray-600">✓ Response received</span>
                </div>
                {/* --- FUNCTION CALLS (Collapsible) --- */}
                {functionCalls.length > 0 && (
                    <details className="mt-3 group">
                        <summary
                            className="cursor-pointer text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                            <span className="transition-transform group-open:rotate-90">▶</span>
                            Function Calls ({functionCalls.length})
                        </summary>

                        <div className="ml-4 mt-2">
                            <ul className="list-disc list-inside text-xs text-gray-600">
                                {functionCalls.map((call, index) => (
                                    <li key={index} className="mt-2">
                                        <strong>{call.name}:</strong>
                                        <pre
                                            className="whitespace-pre-wrap bg-gray-100 p-2 rounded-md border border-gray-200">
                          {JSON.stringify(call.args, null, 2)}
                        </pre>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </details>
                )}

                {/* --- FUNCTION RESPONSES (Collapsible) --- */}
                {functionResponses.length > 0 && (
                    <details className="mt-3 group">
                        <summary
                            className="cursor-pointer text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                            <span className="transition-transform group-open:rotate-90">▶</span>
                            Function Responses ({functionResponses.length})
                        </summary>

                        <div className="ml-4 mt-2">
                            <ul className="list-disc list-inside text-xs text-gray-600">
                                {functionResponses.map((result, index) => {
                                    const functionName = result.name;
                                    const functionResponse = result.response;

                                    return (
                                        <li key={index} className="mt-2">
                                            <strong>{functionName}:</strong>

                                            <pre
                                                className="whitespace-pre-wrap bg-gray-100 p-2 rounded-md border border-gray-200">
                            {JSON.stringify(functionResponse, null, 2)}
                          </pre>

                                            {getFunctionResponseComponent(functionName, functionResponse)}
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    </details>
                )}

            </div>
        </div>
    );
};
