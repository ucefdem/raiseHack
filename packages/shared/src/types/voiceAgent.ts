/** Voice agents in the speech pipeline (wake words + orchestrator). */
export type VoiceAgentId = "angie" | "nikki" | "olaf";

export interface VoiceAgent {
  id: VoiceAgentId;
  name: string;
  wakeWord: string;
  title: string;
  description: string;
  skillPath: string;
  /** When set, this agent is a subagent of the parent manager (e.g. Angie). */
  parentId?: VoiceAgentId;
}
