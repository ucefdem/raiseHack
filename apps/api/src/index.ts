import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { cors } from "hono/cors";
import type {
  Agent,
  ChatRequest,
  Department,
  MeetLink,
  PresenceEvent,
} from "@raisehack/shared";

const app = new Hono();

app.use(
  "*",
  cors({
    origin: process.env.CORS_ORIGIN ?? "http://localhost:3000",
  }),
);

const seedDepartments: Department[] = [
  {
    id: "dept-engineering",
    name: "Engineering",
    description: "Frontend and backend specialists.",
    floor: 1,
    zone: { position: [0, 0.18, 0], size: [5.65, 0.25, 5.65], color: "#3b82f6" },
    meetUrl: "https://meet.google.com/lookup/engineering-room",
    agentIds: ["agent-frontend", "agent-backend"],
  },
  {
    id: "dept-platform",
    name: "Platform & Security",
    description: "DevOps and security teams.",
    floor: 2,
    zone: { position: [0, 3.38, 0], size: [5.65, 0.25, 5.65], color: "#10b981" },
    meetUrl: "https://meet.google.com/lookup/platform-room",
    agentIds: ["agent-devops", "agent-security"],
  },
  {
    id: "dept-product",
    name: "Product & QA",
    description: "QA and product strategy.",
    floor: 3,
    zone: { position: [0, 6.58, 0], size: [5.65, 0.25, 5.65], color: "#f59e0b" },
    meetUrl: "https://meet.google.com/lookup/product-room",
    agentIds: ["agent-qa", "agent-product"],
  },
];

const seedAgents: Agent[] = [
  {
    id: "agent-frontend",
    name: "Alex Chen",
    role: "frontend",
    departmentId: "dept-engineering",
    personaPrompt: "Senior frontend engineer.",
    status: "online",
    createdBy: { name: "Youssef Dem", role: "Engineering Lead", team: "Engineering" },
  },
  {
    id: "agent-backend",
    name: "Sam Rivera",
    role: "backend",
    departmentId: "dept-engineering",
    personaPrompt: "Backend API specialist.",
    status: "online",
    createdBy: { name: "Youssef Dem", role: "Engineering Lead", team: "Engineering" },
  },
  {
    id: "agent-devops",
    name: "Jordan Lee",
    role: "devops",
    departmentId: "dept-platform",
    personaPrompt: "DevOps and CI/CD expert.",
    status: "busy",
    createdBy: { name: "Morgan Blake", role: "Platform Director", team: "Platform" },
  },
  {
    id: "agent-security",
    name: "Morgan Blake",
    role: "security",
    departmentId: "dept-platform",
    personaPrompt: "Security engineer.",
    status: "online",
    createdBy: { name: "Morgan Blake", role: "Platform Director", team: "Platform" },
  },
  {
    id: "agent-qa",
    name: "Taylor Kim",
    role: "qa",
    departmentId: "dept-product",
    personaPrompt: "QA and test strategy.",
    status: "online",
    createdBy: { name: "Riley Morgan", role: "Head of Product", team: "Product" },
  },
  {
    id: "agent-product",
    name: "Riley Morgan",
    role: "product",
    departmentId: "dept-product",
    personaPrompt: "Product manager.",
    status: "offline",
    createdBy: { name: "Victoria Nash", role: "CEO", team: "Executive" },
  },
];

app.get("/health", (c) => c.json({ ok: true }));

app.get("/api/departments", (c) => c.json(seedDepartments));

app.get("/api/agents", (c) => {
  const departmentId = c.req.query("departmentId");
  const agents = departmentId
    ? seedAgents.filter((agent) => agent.departmentId === departmentId)
    : seedAgents;
  return c.json(agents);
});

app.get("/api/agents/:id", (c) => {
  const agent = seedAgents.find((item) => item.id === c.req.param("id"));
  if (!agent) {
    return c.json({ error: "Agent not found" }, 404);
  }
  return c.json(agent);
});

/** Person 2: replace stub with streaming LLM routing */
app.post("/api/chat", async (c) => {
  const body = (await c.req.json()) as ChatRequest;
  const agent = seedAgents.find((item) => item.id === body.agentId);
  if (!agent) {
    return c.json({ error: "Agent not found" }, 404);
  }

  return c.json({
    conversationId: body.conversationId ?? `conv-${Date.now()}`,
    message: {
      id: `msg-${Date.now()}`,
      role: "assistant",
      content: `[${agent.name}] Stub response — Person 2 wires real chat here.`,
      timestamp: new Date().toISOString(),
    },
  });
});

/** Person 3: replace with WebSocket / Supabase Realtime */
app.get("/api/presence", (c) => {
  const stubPresence: PresenceEvent[] = [
    {
      userId: "demo-user-1",
      departmentId: "dept-engineering",
      state: "online",
      timestamp: new Date().toISOString(),
      displayName: "Demo User",
    },
  ];
  return c.json(stubPresence);
});

/** Person 4: Meet launch + join tracking */
app.get("/api/meet/:departmentId", (c) => {
  const department = seedDepartments.find(
    (item) => item.id === c.req.param("departmentId"),
  );
  if (!department?.meetUrl) {
    return c.json({ error: "Meet link not found" }, 404);
  }

  const agentId = c.req.query("agentId");
  const link: MeetLink = {
    departmentId: department.id,
    agentId: agentId ?? undefined,
    url: department.meetUrl,
    label: agentId ? `Meet with agent` : `Meet — ${department.name}`,
  };
  return c.json(link);
});

const port = Number(process.env.PORT ?? 3001);

serve({ fetch: app.fetch, port }, () => {
  console.log(`API running on http://localhost:${port}`);
});
