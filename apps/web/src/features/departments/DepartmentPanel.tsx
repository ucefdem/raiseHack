"use client";

import { useState } from "react";
import type { Agent } from "@raisehack/shared";
import { getAgentsByDepartment } from "@/data/agents";
import { useSelection } from "@/features/selection/SelectionProvider";
import { FloorPlanPreview } from "./FloorPlanPreview";

type PanelTab = "overview" | "structure" | "agents";

const statusStyles: Record<Agent["status"], string> = {
  online: "bg-emerald-400",
  busy: "bg-amber-400",
  offline: "bg-slate-500",
};

function AgentCard({ agent }: { agent: Agent }) {
  const { selectedAgentId, setSelectedAgent } = useSelection();
  const isSelected = selectedAgentId === agent.id;

  return (
    <button
      type="button"
      onClick={() => setSelectedAgent(agent.id)}
      className={`w-full rounded-xl border px-3 py-2.5 text-left transition ${
        isSelected
          ? "border-amber-400/50 bg-amber-400/10"
          : "border-white/8 bg-white/5 hover:border-white/15 hover:bg-white/8"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-white/90">{agent.name}</span>
        <span className="flex items-center gap-1.5 text-[10px] capitalize text-white/45">
          <span className={`h-1.5 w-1.5 rounded-full ${statusStyles[agent.status]}`} />
          {agent.status}
        </span>
      </div>
      <p className="mt-0.5 text-xs capitalize text-white/40">{agent.role}</p>
    </button>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 rounded-lg px-3 py-2 text-xs font-medium transition ${
        active
          ? "bg-white/12 text-white"
          : "text-white/45 hover:text-white/70"
      }`}
    >
      {children}
    </button>
  );
}

export function DepartmentPanel() {
  const { selectedDepartment, selectedAgent, clearSelection } = useSelection();
  const [tab, setTab] = useState<PanelTab>("structure");

  if (!selectedDepartment) {
    return (
      <aside className="flex h-full flex-col rounded-2xl border border-white/10 bg-black/40 p-5 backdrop-blur-2xl">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/35">
          Department
        </p>
        <h2 className="mt-2 text-xl font-light text-white/90">
          Select a floor
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-white/45">
          Click a highlighted balcony in the 3D model or pick a floor on the
          left slider to inspect a department.
        </p>
        <div className="mt-6 rounded-xl border border-dashed border-white/10 p-6 text-center text-xs text-white/30">
          No floor selected
        </div>
      </aside>
    );
  }

  const departmentAgents = getAgentsByDepartment(selectedDepartment.id);
  const onlineCount = departmentAgents.filter((a) => a.status === "online").length;

  return (
    <aside className="flex h-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-black/40 backdrop-blur-2xl">
      {/* Tab bar — matches reference Overview / Structure / Advice */}
      <div className="flex gap-1 border-b border-white/8 p-2">
        <TabButton active={tab === "overview"} onClick={() => setTab("overview")}>
          Overview
        </TabButton>
        <TabButton active={tab === "structure"} onClick={() => setTab("structure")}>
          Structure
        </TabButton>
        <TabButton active={tab === "agents"} onClick={() => setTab("agents")}>
          Agents
        </TabButton>
      </div>

      <div className="flex flex-1 flex-col overflow-y-auto p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-400/80">
              Floor {selectedDepartment.floor}
            </p>
            <h2 className="mt-1 text-xl font-light text-white">
              {selectedDepartment.name}
            </h2>
          </div>
          <button
            type="button"
            onClick={clearSelection}
            className="shrink-0 rounded-lg px-2 py-1 text-[10px] text-white/35 hover:bg-white/8 hover:text-white/60"
          >
            ✕
          </button>
        </div>

        {tab === "overview" && (
          <div className="mt-4 space-y-4">
            <p className="text-sm leading-relaxed text-white/50">
              {selectedDepartment.description}
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-white/8 bg-white/5 p-3">
                <p className="text-[10px] uppercase tracking-wider text-white/35">
                  Agents
                </p>
                <p className="mt-1 text-2xl font-light text-white">
                  {departmentAgents.length}
                </p>
              </div>
              <div className="rounded-xl border border-white/8 bg-white/5 p-3">
                <p className="text-[10px] uppercase tracking-wider text-white/35">
                  Online
                </p>
                <p className="mt-1 text-2xl font-light text-emerald-400">
                  {onlineCount}
                </p>
              </div>
            </div>
            {selectedDepartment.meetUrl && (
              <a
                href={selectedDepartment.meetUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center justify-center rounded-xl bg-amber-400 px-4 py-3 text-sm font-medium text-slate-900 transition hover:bg-amber-300"
              >
                Open 3D Tour →
              </a>
            )}
          </div>
        )}

        {tab === "structure" && (
          <div className="mt-4 space-y-4">
            <FloorPlanPreview department={selectedDepartment} />
            <div className="rounded-xl border border-white/8 bg-white/5 p-3">
              <p className="text-[10px] uppercase tracking-wider text-white/35">
                Total area
              </p>
              <p className="mt-1 text-lg font-light text-white/80">
                {(departmentAgents.length * 42.8).toFixed(1)} sq.m
              </p>
              <p className="mt-1 text-xs text-white/35">
                Floor {selectedDepartment.floor} · {departmentAgents.length} agent stations
              </p>
            </div>
          </div>
        )}

        {tab === "agents" && (
          <div className="mt-4 space-y-2">
            {departmentAgents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
            {selectedAgent && (
              <div className="mt-3 rounded-xl border border-amber-400/25 bg-amber-400/8 p-3">
                <p className="text-[10px] uppercase tracking-wider text-amber-400/70">
                  Active selection
                </p>
                <p className="mt-1 text-sm font-medium text-white">
                  {selectedAgent.name}
                </p>
                <p className="text-xs capitalize text-white/45">
                  {selectedAgent.role}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
