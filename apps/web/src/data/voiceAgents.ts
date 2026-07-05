import type { VoiceAgent, VoiceAgentId } from "@raisehack/shared";

/** Angie is the manager; Nikki and Olaf are subagents she delegates to. */
export const voiceAgents: Record<VoiceAgentId, VoiceAgent> = {
  angie: {
    id: "angie",
    name: "Angie",
    wakeWord: "Angie",
    title: "Meeting Manager",
    description:
      "Joins Meet to triage incidents and customer complaints. Delegates code fixes to Nikki.",
    skillPath: "agents/angie/SKILL.md",
  },
  nikki: {
    id: "nikki",
    name: "Nikki",
    wakeWord: "Nikki",
    title: "Code Subagent",
    description: "Reads mock-incident/ locally, finds bugs, and describes fixes — invoked by Angie.",
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
