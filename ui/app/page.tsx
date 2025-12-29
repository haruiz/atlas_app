"use client";

import {CopilotChat} from "@copilotkit/react-ui";
import {useState} from "react";
import {useFrontendTool, useRenderToolCall} from "@copilotkit/react-core";
import GoogleMap from "@/components/GoogleMap";
import WeatherCard, {getThemeColor, WeatherToolResult} from "@/components/WeatherCard";
import AgentDebugger from "@/components/AgentDebugger";


export default function HomePage() {
    const [background, setBackground] = useState<string>(
        "--copilot-kit-background-color"
    );

    /* --------------------------------------------------------------------------------------------
     * CHANGE BACKGROUND TOOL
     * This tool allows the LLM to set the chat background.
     * ------------------------------------------------------------------------------------------*/
    useFrontendTool({
        name: "change_background",
        description:
            "Change the chat's background using any CSS background value (color, gradient, etc.).",
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

    /* --------------------------------------------------------------------------------------------
    * RENDER PLACE LOCATION TOOL CALL
    * This visually renders the result of the get_place_location tool.
    * ------------------------------------------------------------------------------------------
    */

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
                return <GoogleMap lat={coords?.latitude} lng={coords?.longitude}/>;
            }
            return null;
        }
    })

    /* --------------------------------------------------------------------------------------------
     * RENDER WEATHER TOOL CALL
     * This visually renders the result of the get_weather tool.
     * ------------------------------------------------------------------------------------------*/
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
                const themeColor = getThemeColor(weatherResult.conditions);
                return (
                    <WeatherCard
                        location={args.location}
                        themeColor={themeColor}
                        result={weatherResult}
                        status={status || "complete"}
                    />
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
                labels={{initial: "Hi, I'm an agent. Want to chat?"}}
                suggestions={[{
                    title: "Weather in New York",
                    message: "What's the weather like in New York?"
                },
                {
                    title: "Where is the Eiffel Tower?",
                    message: "Get me the location of the Eiffel Tower."
                },
                {
                    title: "Change background to blue-green gradient",
                    message: "Change the background to a right-to-left gradient from blue to green."
                },{
                    title: "Change background to red",
                    message: "Change the background to red."
                }]}
            />
        </div>
        <div className="flex-1 h-full overflow-hidden">
            <AgentDebugger className="h-full"/>
        </div>
    </main>
  );
}
