import type { Agent } from "@raisehack/shared";
import { SHARED_MEET_URL } from "@/lib/meetLink";

export const agents: Agent[] = [
  {
    id: "agent-angie",
    name: "Angie",
    role: "orchestrator",
    departmentId: "dept-ai-command",
    personaPrompt:
      "You are Angie, the incident orchestrator. You join Google Meet calls, triage customer complaints and outages, and delegate code fixes to Nikki in the local mock codebase.",
    status: "online",
    createdBy: { name: "AI Command", role: "Manager", team: "Voice Agents" },
    meetUrl: SHARED_MEET_URL,
    voiceAgentId: "angie",
    workSurface: "browser",
  },
  {
    id: "agent-frontend",
    name: "Alex Chen",
    role: "frontend",
    departmentId: "dept-engineering",
    personaPrompt:
      "You are a senior frontend engineer focused on React, UX, and performance.",
    status: "online",
    createdBy: { name: "Youssef Dem", role: "Engineering Lead", team: "Engineering" },
    meetUrl: SHARED_MEET_URL,
    workSurface: "browser",
  },
  {
    id: "agent-backend",
    name: "Sam Rivera",
    role: "backend",
    departmentId: "dept-engineering",
    personaPrompt:
      "You are a backend engineer specializing in APIs, databases, and system design.",
    status: "online",
    createdBy: { name: "Youssef Dem", role: "Engineering Lead", team: "Engineering" },
    meetUrl: SHARED_MEET_URL,
    workSurface: "ide",
    error: {
      message: "Integration test suite failed on chat-service PR #142",
      severity: "critical",
      needsReview: true,
    },
  },
  {
    id: "agent-devops",
    name: "Jordan Lee",
    role: "devops",
    departmentId: "dept-platform",
    personaPrompt:
      "You are a DevOps engineer focused on CI/CD, infrastructure, and reliability.",
    status: "busy",
    createdBy: { name: "Morgan Blake", role: "Platform Director", team: "Platform" },
    meetUrl: SHARED_MEET_URL,
    workSurface: "terminal",
    error: {
      message: "Staging deploy pipeline stuck — rollback recommended",
      severity: "warning",
      needsReview: true,
    },
  },
  {
    id: "agent-security",
    name: "Morgan Blake",
    role: "security",
    departmentId: "dept-platform",
    personaPrompt:
      "You are a security engineer focused on threat modeling and secure defaults.",
    status: "online",
    createdBy: { name: "Morgan Blake", role: "Platform Director", team: "Platform" },
    meetUrl: SHARED_MEET_URL,
    workSurface: "browser",
  },
  {
    id: "agent-qa",
    name: "Taylor Kim",
    role: "qa",
    departmentId: "dept-product",
    personaPrompt:
      "You are a QA engineer focused on test strategy, edge cases, and quality gates.",
    status: "online",
    createdBy: { name: "Riley Morgan", role: "Head of Product", team: "Product" },
    meetUrl: SHARED_MEET_URL,
    workSurface: "jira",
  },
  {
    id: "agent-product",
    name: "Riley Morgan",
    role: "product",
    departmentId: "dept-product",
    personaPrompt:
      "You are a product manager focused on user needs, scope, and prioritization.",
    status: "offline",
    createdBy: { name: "Victoria Nash", role: "CEO", team: "Executive" },
    meetUrl: SHARED_MEET_URL,
    workSurface: "browser",
  },
  {
    id: "agent-sales",
    name: "Casey Brooks",
    role: "sales",
    departmentId: "dept-sales",
    personaPrompt:
      "You are an enterprise AE focused on pipeline, demos, and customer outcomes.",
    status: "busy",
    createdBy: { name: "Victoria Nash", role: "CEO", team: "Executive" },
    meetUrl: SHARED_MEET_URL,
    workSurface: "browser",
  },
  {
    id: "agent-ceo",
    name: "Victoria Nash",
    role: "executive",
    departmentId: "dept-executive",
    personaPrompt:
      "You are the CEO agent — company strategy, investor updates, and cross-team alignment.",
    status: "online",
    createdBy: { name: "Victoria Nash", role: "CEO", team: "Executive" },
    meetUrl: SHARED_MEET_URL,
    workSurface: "none",
  },
];

export function getAgentById(id: string): Agent | undefined {
  return agents.find((agent) => agent.id === id);
}

export function getAgentsByDepartment(departmentId: string): Agent[] {
  return agents.filter((agent) => agent.departmentId === departmentId);
}

export function getAgentsWithErrors(): Agent[] {
  return agents.filter((agent) => agent.error?.needsReview);
}
