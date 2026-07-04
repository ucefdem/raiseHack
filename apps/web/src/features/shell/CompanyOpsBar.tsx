"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  Coins,
  ExternalLink,
  LayoutList,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";
import {
  companyKpis,
  getTotalTokenBudget,
  getTotalTokenSpend,
  jiraTickets,
  tokenSpend,
  type JiraTicket,
} from "@/data/companyOps";

export type OpsPanel = "kpi" | "tokens" | "jira" | null;

const panelTitles: Record<Exclude<OpsPanel, null>, string> = {
  kpi: "Company KPI",
  tokens: "Token spend",
  jira: "Jira",
};

const jiraStatusColor: Record<JiraTicket["status"], string> = {
  "To Do": "text-white/45 bg-white/10",
  "In Progress": "text-amber-300 bg-amber-400/15",
  "In Review": "text-blue-300 bg-blue-400/15",
  Done: "text-emerald-300 bg-emerald-400/15",
};

const priorityColor: Record<JiraTicket["priority"], string> = {
  Low: "text-white/35",
  Medium: "text-white/55",
  High: "text-amber-400",
  Critical: "text-red-400",
};

function KpiContent() {
  return (
    <div className="grid grid-cols-2 gap-3">
      {companyKpis.map((kpi) => (
        <div
          key={kpi.id}
          className="rounded-xl border border-white/8 bg-white/5 p-3"
        >
          <p className="text-[10px] uppercase tracking-wider text-white/35">
            {kpi.label}
          </p>
          <p className="mt-1 text-xl font-light text-white">{kpi.value}</p>
          <div className="mt-1 flex items-center gap-1 text-xs">
            {kpi.trend === "up" && (
              <TrendingUp className="h-3 w-3 text-emerald-400" />
            )}
            {kpi.trend === "down" && (
              <TrendingDown className="h-3 w-3 text-red-400" />
            )}
            <span
              className={
                kpi.trend === "up"
                  ? "text-emerald-400"
                  : kpi.trend === "down"
                    ? "text-red-400"
                    : "text-white/45"
              }
            >
              {kpi.change}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function TokensContent() {
  const total = getTotalTokenSpend();
  const budget = getTotalTokenBudget();
  const pct = Math.round((total / budget) * 100);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-white/8 bg-white/5 p-4">
        <p className="text-[10px] uppercase tracking-wider text-white/35">
          Total this month
        </p>
        <p className="mt-1 text-2xl font-light text-white">
          {(total / 1_000_000).toFixed(2)}M
          <span className="ml-1 text-sm text-white/40">/ {(budget / 1_000_000).toFixed(1)}M tokens</span>
        </p>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-emerald-400 transition-all"
            style={{ width: `${Math.min(pct, 100)}%` }}
          />
        </div>
        <p className="mt-1 text-xs text-white/40">{pct}% of monthly budget</p>
      </div>

      <ul className="space-y-2">
        {tokenSpend.map((row) => {
          const rowPct = Math.round((row.tokens / row.budget) * 100);
          return (
            <li
              key={row.department}
              className="rounded-lg border border-white/8 bg-white/5 px-3 py-2.5"
            >
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/75">{row.department}</span>
                <span className="tabular-nums text-white/45">
                  {(row.tokens / 1000).toFixed(0)}k / {(row.budget / 1000).toFixed(0)}k
                </span>
              </div>
              <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/10">
                <div
                  className={`h-full rounded-full ${rowPct > 85 ? "bg-amber-400" : "bg-emerald-400/80"}`}
                  style={{ width: `${Math.min(rowPct, 100)}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function JiraContent() {
  return (
    <ul className="space-y-2">
      {jiraTickets.map((ticket) => (
        <li
          key={ticket.id}
          className="rounded-lg border border-white/8 bg-white/5 px-3 py-2.5"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-emerald-400/80">
                  {ticket.key}
                </span>
                <span
                  className={`rounded px-1.5 py-0.5 text-[9px] font-medium ${jiraStatusColor[ticket.status]}`}
                >
                  {ticket.status}
                </span>
              </div>
              <p className="mt-1 text-sm text-white/80">{ticket.summary}</p>
              <p className="mt-1 text-xs text-white/40">{ticket.assignee}</p>
            </div>
            <span className={`shrink-0 text-[10px] font-medium ${priorityColor[ticket.priority]}`}>
              {ticket.priority}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

interface CompanyOpsBarProps {
  activePanel: OpsPanel;
  onPanelChange: (panel: OpsPanel) => void;
}

export function CompanyOpsBar({ activePanel, onPanelChange }: CompanyOpsBarProps) {
  const buttons: { id: Exclude<OpsPanel, null>; label: string; icon: React.ReactNode }[] = [
    { id: "kpi", label: "Company KPI", icon: <BarChart3 className="h-3.5 w-3.5" /> },
    { id: "tokens", label: "Token spend", icon: <Coins className="h-3.5 w-3.5" /> },
    { id: "jira", label: "Jira", icon: <LayoutList className="h-3.5 w-3.5" /> },
  ];

  return (
    <div className="pointer-events-auto absolute right-5 top-5 z-20 flex items-center gap-1.5 sm:right-8">
      {buttons.map(({ id, label, icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => onPanelChange(activePanel === id ? null : id)}
          className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-medium transition ${
            activePanel === id
              ? "border-emerald-400/50 bg-emerald-400/15 text-emerald-200"
              : "border-white/10 bg-black/35 text-white/60 backdrop-blur-xl hover:border-white/25 hover:text-white"
          }`}
        >
          {icon}
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}

interface CompanyOpsPanelProps {
  panel: OpsPanel;
  onClose: () => void;
}

export function CompanyOpsPanel({ panel, onClose }: CompanyOpsPanelProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (panel) {
      requestAnimationFrame(() => setVisible(true));
    } else {
      setVisible(false);
    }
  }, [panel]);

  if (!panel) return null;

  return (
    <div
      className={`pointer-events-auto fixed right-5 top-16 z-30 flex w-[min(380px,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-2xl border border-white/10 bg-black/50 shadow-2xl shadow-black/40 backdrop-blur-2xl transition-all duration-300 sm:right-8 sm:top-[4.5rem] ${
        visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
      }`}
      style={{ maxHeight: "calc(100vh - 6rem)" }}
    >
      <div className="flex items-center justify-between border-b border-white/8 px-4 py-3">
        <h2 className="text-sm font-medium text-white">{panelTitles[panel]}</h2>
        <div className="flex items-center gap-1">
          {panel === "jira" && (
            <a
              href="https://jira.atlassian.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex h-7 w-7 items-center justify-center rounded-lg text-white/40 transition hover:bg-white/10 hover:text-white"
              title="Open Jira"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex h-7 w-7 items-center justify-center rounded-lg text-white/40 transition hover:bg-white/10 hover:text-white"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {panel === "kpi" && <KpiContent />}
        {panel === "tokens" && <TokensContent />}
        {panel === "jira" && <JiraContent />}
      </div>
    </div>
  );
}
