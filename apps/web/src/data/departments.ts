import type { Department } from "@raisehack/shared";
import { makeDepartmentZone } from "@/features/scene/buildingConfig";

export const departments: Department[] = [
  {
    id: "dept-engineering",
    name: "Engineering",
    description: "Frontend and backend specialists building the product.",
    floor: 1,
    zone: makeDepartmentZone(1, "#059669"),
    meetUrl: "https://meet.google.com/lookup/engineering-room",
    agentIds: ["agent-frontend", "agent-backend"],
    missionPlan: {
      mission: "Ship reliable product increments every sprint.",
      goals: [
        "Reduce p95 API latency below 120ms",
        "Launch agent chat v2 with streaming",
        "Maintain 85%+ test coverage on core paths",
      ],
      calendar: [
        { id: "eng-1", title: "Sprint planning", date: "Mon 10:00", status: "planned" },
        { id: "eng-2", title: "Architecture review — chat service", date: "Wed 14:00", status: "in-progress" },
        { id: "eng-3", title: "Release candidate cut", date: "Fri 16:00", status: "planned" },
      ],
    },
  },
  {
    id: "dept-platform",
    name: "Platform & Security",
    description: "DevOps and security teams keeping systems safe and running.",
    floor: 2,
    zone: makeDepartmentZone(2, "#2563eb"),
    meetUrl: "https://meet.google.com/lookup/platform-room",
    agentIds: ["agent-devops", "agent-security"],
    missionPlan: {
      mission: "Keep production healthy and secure at scale.",
      goals: [
        "Zero critical vulns in production deps",
        "Deploy staging in under 8 minutes",
        "Complete SOC2 control mapping Q2",
      ],
      calendar: [
        { id: "plat-1", title: "Incident retro — deploy pipeline", date: "Tue 09:30", status: "in-progress" },
        { id: "plat-2", title: "Security office hours", date: "Thu 11:00", status: "planned" },
      ],
    },
  },
  {
    id: "dept-product",
    name: "Product & QA",
    description: "Quality assurance and product strategy for user outcomes.",
    floor: 2,
    zone: makeDepartmentZone(2, "#8b5cf6"),
    meetUrl: "https://meet.google.com/lookup/product-room",
    agentIds: ["agent-qa", "agent-product"],
    missionPlan: {
      mission: "Validate what we build matches what users need.",
      goals: [
        "Close 12 P0 bugs before GA",
        "Publish Q3 roadmap draft",
        "Run 5 user tests on 3D office flow",
      ],
      calendar: [
        { id: "prod-1", title: "QA sign-off — agent modal", date: "Tue 15:00", status: "in-progress" },
        { id: "prod-2", title: "Stakeholder demo", date: "Thu 10:00", status: "planned" },
      ],
    },
  },
  {
    id: "dept-sales",
    name: "Sales",
    description: "Enterprise pipeline, demos, and customer success handoffs.",
    floor: 3,
    zone: makeDepartmentZone(3, "#f59e0b"),
    meetUrl: "https://meet.google.com/lookup/sales-room",
    agentIds: ["agent-sales"],
    missionPlan: {
      mission: "Grow ARR through qualified enterprise deals.",
      goals: [
        "Close 3 pilot contracts this quarter",
        "Reduce demo-to-close cycle to 21 days",
        "Launch self-serve pricing page",
      ],
      calendar: [
        { id: "sales-1", title: "Acme Corp demo", date: "Mon 13:00", status: "in-progress" },
        { id: "sales-2", title: "Pipeline review with CEO", date: "Wed 09:00", status: "planned" },
      ],
    },
  },
  {
    id: "dept-executive",
    name: "Executive",
    description: "CEO office — strategy, investors, and company-wide alignment.",
    floor: 3,
    zone: makeDepartmentZone(3, "#dc2626"),
    meetUrl: "https://meet.google.com/lookup/executive-room",
    agentIds: ["agent-ceo"],
    missionPlan: {
      mission: "Align the company on vision, metrics, and execution.",
      goals: [
        "Hit $2M ARR run-rate by Q4",
        "Finalize Series A data room",
        "Roll out agent workforce policy",
      ],
      calendar: [
        { id: "exec-1", title: "Board prep session", date: "Tue 08:00", status: "in-progress" },
        { id: "exec-2", title: "All-hands — agent HQ demo", date: "Fri 11:00", status: "planned" },
      ],
    },
  },
];

export function getDepartmentById(id: string): Department | undefined {
  return departments.find((department) => department.id === id);
}

export function getDepartmentsByFloor(floor: number): Department[] {
  return departments.filter((department) => department.floor === floor);
}
