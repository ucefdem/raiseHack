import type { AgentActivity } from "@raisehack/shared";

export const agentActivities: AgentActivity[] = [
  {
    agentId: "agent-frontend",
    task: "Polishing the dashboard UI components",
    location: "Design desk · Floor 1",
    mood: "In the flow",
    progress: 72,
  },
  {
    agentId: "agent-backend",
    task: "Debugging failing integration tests on chat-service",
    location: "Pairing station · Floor 1",
    mood: "Blocked — needs review",
    progress: 45,
  },
  {
    agentId: "agent-devops",
    task: "Investigating stuck staging deployment",
    location: "Ops corner · Floor 2",
    mood: "Alert",
    progress: 88,
  },
  {
    agentId: "agent-security",
    task: "Running dependency vulnerability scan",
    location: "Secure pod · Floor 2",
    mood: "Alert",
    progress: 30,
  },
  {
    agentId: "agent-qa",
    task: "Working in Jira — triaging agent chat tickets",
    location: "Test lab · Floor 3",
    mood: "Methodical",
    progress: 55,
  },
  {
    agentId: "agent-product",
    task: "Drafting sprint priorities with stakeholders",
    location: "Lounge · Floor 3",
    mood: "Collaborative",
    progress: 20,
  },
  {
    agentId: "agent-sales",
    task: "Prepping enterprise demo deck for Acme Corp",
    location: "Sales pod · Floor 3",
    mood: "Pitch mode",
    progress: 65,
  },
  {
    agentId: "agent-ceo",
    task: "Reviewing company KPI dashboard and board deck",
    location: "Corner office · Floor 3",
    mood: "Strategic",
    progress: 40,
  },
];

export function getActivityByAgentId(agentId: string): AgentActivity | undefined {
  return agentActivities.find((a) => a.agentId === agentId);
}
