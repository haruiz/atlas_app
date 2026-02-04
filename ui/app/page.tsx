"use client";

import React, {useEffect} from "react";
import "@copilotkit/react-ui/styles.css";
// import "./style.css";

// CopilotKit core
import {useCopilotAction, useCopilotChat,} from "@copilotkit/react-core";
import {CopilotChat} from "@copilotkit/react-ui";
import {MessageToA2A} from "@/components/a2a/MessageToA2A";
import {MessageFromA2A} from "@/components/a2a/MessageFromA2A";



const Chat = () => {
    const {visibleMessages} = useCopilotChat();

    useCopilotAction({
    name: "send_message_to_a2a_agent",
    description: "Sends a message to an A2A agent",
    available: "frontend",
    parameters: [
      {
        name: "agentName",
        type: "string",
        description: "The name of the A2A agent to send the message to",
      },
      {
        name: "task",
        type: "string",
        description: "The message to send to the A2A agent",
      },
    ],
    render: (actionRenderProps) => {
        console.log(actionRenderProps);
      return (
        <>
          <MessageToA2A {...actionRenderProps} />
          <MessageFromA2A {...actionRenderProps} />
        </>
      );
    },
  });

    useEffect(() => {
      const extractDataFromMessages = () => {
      for (const message of visibleMessages) {
        const msg = message;

        if (msg.type === "ResultMessage" && msg.actionName === "send_message_to_a2a_agent") {

          try {
            let parsed;
            const result = msg.result;
            if (typeof result === "string") {
              try {
                  parsed = JSON.parse(result);
              }
            catch {
                continue;
            }
            } else if (typeof result === "object") {
                parsed = result;
            }
            console.log("Sending message to A2A agent: ", parsed);
          } catch (e) {
            console.error("Failed to extract data from message:", e);
          }
        }
      }
    };

    extractDataFromMessages();
    }, [visibleMessages]);

    /* --------------------------------------------------------------------------------------------
     * MAIN UI RENDERING
     * ------------------------------------------------------------------------------------------*/
    return (
        <div
            className="flex justify-center items-center h-full w-full"
            data-testid="background-container"
        >
            <div className="h-full w-full md:w-8/10 md:h-8/10 rounded-lg">
                <CopilotChat
                    onSubmitMessage={(message) => {
                        console.log("User submitted message:", message);
                    }}
                    suggestions={[{
                        title: "What is the weather in San Francisco?",
                        message: "What is the weather in San Francisco?"
                    }]}
                    className="h-full rounded-2xl max-w-6xl mx-auto"
                    labels={{initial: "Hi, I'm an agent. Want to chat?"}}
                />
            </div>
            <span className="absolute bottom-4 right-4 text-xs text-gray-400">
                Num Messages: {visibleMessages.length}
            </span>
        </div>
    );
};

/* ------------------------------------------------------------------------------------------------
 * HOME PAGE WRAPPER
 * ----------------------------------------------------------------------------------------------*/

const HomePage = () => {
    return (
        <main className="h-screen w-screen">
            <Chat/>
        </main>
    );
};

export default HomePage;
