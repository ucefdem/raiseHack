export type AgentRole =
  | "frontend"
  | "backend"
  | "devops"
  | "qa"
  | "security"
  | "design"
  | "product"
  | "data"
  | "sales"
  | "executive";

export type AgentStatus = "online" | "busy" | "offline";

/** Fake workstation UI shown above busy agents in the 3D scene */
export type AgentWorkSurface = "browser" | "ide" | "jira" | "terminal" | "none";

export interface AgentCreator {
  name: string;
  role: string;
  team?: string;
}

export interface AgentError {
  message: string;
  severity: "warning" | "critical";
  needsReview: true;
}

export interface Agent {
  id: string;
  name: string;
  role: AgentRole;
  departmentId: string;
  personaPrompt: string;
  status: AgentStatus;
  /** Who provisioned / owns this agent in the org */
  createdBy: AgentCreator;
  /** Per-agent meet link (1:1 or agent room) */
  meetUrl?: string;
  /** Visual workstation prop when agent is active */
  workSurface?: AgentWorkSurface;
  /** When set, agent needs human review */
  error?: AgentError;
  tools?: string[];
  availability?: string;
}
