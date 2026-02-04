

export type AgentStyle = {
  bgColor: string;
  textColor: string;
  borderColor: string;
  icon: string;
  framework?: string;
};

export function getAgentStyle(agentName: string): AgentStyle {
  if (!agentName) {
    return defaultStyle();
  }

  const name = agentName.toLowerCase();

  if (name.includes("weather")) {
    return {
      bgColor: "bg-gradient-to-r from-emerald-100 to-green-100",
      textColor: "text-emerald-800",
      borderColor: "border-emerald-400",
      icon: "⛅️",
      framework: "ADK",
    };
  }

  if (name.includes("maps")) {
    return {
      bgColor: "bg-gradient-to-r from-blue-100 to-sky-100",
      textColor: "text-blue-800",
      borderColor: "border-blue-400",
      icon: "🗺️",
      framework: "ADK",
    };
  }

  return defaultStyle();
}

function defaultStyle(): AgentStyle {
  return {
    bgColor: "bg-gray-100",
    textColor: "text-gray-700",
    borderColor: "border-gray-300",
    icon: "🤖",
    framework: "",
  };
}

export function truncateTask(text: string, maxLength: number = 50): string {
  return text.length <= maxLength ? text : text.substring(0, maxLength) + "...";
}
