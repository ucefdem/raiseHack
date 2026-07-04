export interface CompanyKpi {
  id: string;
  label: string;
  value: string;
  change: string;
  trend: "up" | "down" | "flat";
}

export interface TokenSpendRow {
  department: string;
  tokens: number;
  budget: number;
  period: string;
}

export interface JiraTicket {
  id: string;
  key: string;
  summary: string;
  status: "To Do" | "In Progress" | "In Review" | "Done";
  assignee: string;
  priority: "Low" | "Medium" | "High" | "Critical";
}

export const companyKpis: CompanyKpi[] = [
  { id: "arr", label: "ARR run-rate", value: "$1.84M", change: "+12%", trend: "up" },
  { id: "agents", label: "Active agents", value: "8", change: "+2", trend: "up" },
  { id: "uptime", label: "Platform uptime", value: "99.7%", change: "-0.1%", trend: "down" },
  { id: "nps", label: "Customer NPS", value: "62", change: "+4", trend: "up" },
  { id: "velocity", label: "Sprint velocity", value: "47 pts", change: "+6", trend: "up" },
  { id: "errors", label: "Agents needing review", value: "2", change: "+1", trend: "down" },
];

export const tokenSpend: TokenSpendRow[] = [
  { department: "Engineering", tokens: 842_000, budget: 1_000_000, period: "This month" },
  { department: "Platform & Security", tokens: 612_000, budget: 750_000, period: "This month" },
  { department: "Product & QA", tokens: 388_000, budget: 500_000, period: "This month" },
  { department: "Sales", tokens: 210_000, budget: 350_000, period: "This month" },
  { department: "Executive", tokens: 95_000, budget: 150_000, period: "This month" },
];

export const jiraTickets: JiraTicket[] = [
  {
    id: "1",
    key: "RH-142",
    summary: "Chat-service integration tests failing on staging",
    status: "In Progress",
    assignee: "Sam Rivera",
    priority: "Critical",
  },
  {
    id: "2",
    key: "RH-138",
    summary: "Staging deploy pipeline stuck — rollback needed",
    status: "In Review",
    assignee: "Jordan Lee",
    priority: "High",
  },
  {
    id: "3",
    key: "RH-129",
    summary: "Agent modal — follow selected agent in viewport",
    status: "Done",
    assignee: "Alex Chen",
    priority: "Medium",
  },
  {
    id: "4",
    key: "RH-131",
    summary: "Floor mission popup with 2D open-space plan",
    status: "In Progress",
    assignee: "Taylor Kim",
    priority: "Medium",
  },
  {
    id: "5",
    key: "RH-125",
    summary: "Enterprise demo deck for Acme Corp",
    status: "To Do",
    assignee: "Casey Brooks",
    priority: "High",
  },
];

export function getTotalTokenSpend(): number {
  return tokenSpend.reduce((sum, row) => sum + row.tokens, 0);
}

export function getTotalTokenBudget(): number {
  return tokenSpend.reduce((sum, row) => sum + row.budget, 0);
}
