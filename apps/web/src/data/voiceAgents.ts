import type { VoiceAgent, VoiceAgentId } from "@raisehack/shared";

/** Angie is the manager; Nikki and Olaf are subagents she delegates to. */
export const voiceAgents: Record<VoiceAgentId, VoiceAgent> = {
  angie: {
    id: "angie",
    name: "Angie",
    wakeWord: "Angie",
    title: "Meeting Manager",
    description:
      "Your single voice interface in Meet. Angie coordinates the call and delegates to Nikki or Olaf when needed.",
    skillPath: "agents/angie/SKILL.md",
  },
  nikki: {
    id: "nikki",
    name: "Nikki",
    wakeWord: "Nikki",
    title: "Sales Subagent",
    description: "Jira tickets, CRM, pipeline, and deal status — invoked by Angie.",
    skillPath: "agents/nikki/SKILL.md",
    parentId: "angie",
  },
  olaf: {
    id: "olaf",
    name: "Olaf",
    wakeWord: "Olaf",
    title: "Computer-Use Subagent",
    description: "Screen share, open URLs, and show dashboards — invoked by Angie.",
    skillPath: "agents/olaf/SKILL.md",
    parentId: "angie",
  },
};

export const angieSubagents: VoiceAgentId[] = ["nikki", "olaf"];

export function getVoiceAgent(id: VoiceAgentId): VoiceAgent {
  return voiceAgents[id];
}

export function getAngieSubagents(): VoiceAgent[] {
  return angieSubagents.map((id) => voiceAgents[id]);
}
