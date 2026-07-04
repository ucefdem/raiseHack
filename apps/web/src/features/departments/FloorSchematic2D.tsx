"use client";

import { Monitor, Users, Video } from "lucide-react";
import type { Agent, Department } from "@raisehack/shared";
import { getAgentsByDepartment } from "@/data/agents";
import { getActivityByAgentId } from "@/data/agentActivities";
import { getMeetingRoomsForDepartment } from "@/data/meetingRooms";
import { useSelection } from "@/features/selection/SelectionProvider";

const surfaceLabel: Record<NonNullable<Agent["workSurface"]>, string> = {
  browser: "Browser",
  ide: "Coding",
  jira: "Jira",
  terminal: "Terminal",
  none: "Idle",
};

const statusDot: Record<Agent["status"], string> = {
  online: "bg-emerald-400",
  busy: "bg-amber-400",
  offline: "bg-slate-500",
};

function AgentDeskCube({
  agent,
  accent,
  onOpen,
}: {
  agent: Agent;
  accent: string;
  onOpen: (id: string) => void;
}) {
  const activity = getActivityByAgentId(agent.id);
  const hasError = agent.error?.needsReview;

  return (
    <button
      type="button"
      onClick={() => onOpen(agent.id)}
      className={`group relative flex flex-col gap-1.5 rounded-lg border p-2.5 text-left transition hover:-translate-y-0.5 ${
        hasError
          ? "border-red-500/50 bg-red-500/10"
          : "border-white/10 bg-white/5 hover:border-white/25"
      }`}
    >
      {/* Screen */}
      <div
        className="flex items-center gap-1 rounded-md border px-1.5 py-1 text-[9px] font-medium"
        style={{
          borderColor: `${accent}55`,
          background: `${accent}18`,
          color: accent,
        }}
      >
        <Monitor className="h-2.5 w-2.5" />
        <span className="truncate">
          {agent.workSurface ? surfaceLabel[agent.workSurface] : "Idle"}
        </span>
      </div>

      {/* Desk / occupant */}
      <div className="flex items-center gap-2">
        <span
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[9px] font-semibold text-slate-900"
          style={{ background: accent }}
        >
          {agent.name
            .split(" ")
            .map((p) => p[0])
            .join("")
            .slice(0, 2)}
        </span>
        <div className="min-w-0">
          <p className="truncate text-[11px] font-medium text-white/85">
            {agent.name}
          </p>
          <div className="flex items-center gap-1">
            <span className={`h-1.5 w-1.5 rounded-full ${statusDot[agent.status]}`} />
            <span className="truncate text-[9px] capitalize text-white/40">
              {agent.role}
            </span>
          </div>
        </div>
      </div>

      {activity && (
        <p className="truncate text-[9px] text-white/40">{activity.task}</p>
      )}

      {hasError && (
        <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
          !
        </span>
      )}
    </button>
  );
}

/** Top-down open-space schematic — lighter alternative to the 3D floor */
export function FloorSchematic2D({ department }: { department: Department }) {
  const { setSelectedAgent } = useSelection();
  const accent = department.zone.color ?? "#4ade80";
  const agents = getAgentsByDepartment(department.id);
  const rooms = getMeetingRoomsForDepartment(department.id);

  return (
    <div className="rounded-xl border border-white/10 bg-black/30 p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-white/45">
          Open space · Floor {department.floor}
        </p>
        <span className="flex items-center gap-1 text-[10px] text-white/35">
          <Users className="h-3 w-3" />
          {agents.length}
        </span>
      </div>

      {/* Open-plan desk grid */}
      <div
        className="relative rounded-lg border border-dashed p-3"
        style={{ borderColor: `${accent}33` }}
      >
        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
          {agents.map((agent) => (
            <AgentDeskCube
              key={agent.id}
              agent={agent}
              accent={accent}
              onOpen={setSelectedAgent}
            />
          ))}
        </div>

        {/* Meeting rooms strip */}
        {rooms.length > 0 && (
          <div className="mt-3 border-t border-white/8 pt-3">
            <p className="mb-2 text-[9px] uppercase tracking-widest text-white/35">
              Meeting rooms
            </p>
            <div className="flex flex-wrap gap-2">
              {rooms.map((room) => (
                <a
                  key={room.id}
                  href={room.meetUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1.5 text-[10px] text-white/70 transition hover:border-white/25 hover:text-white"
                >
                  <Video className="h-3 w-3" style={{ color: accent }} />
                  {room.name}
                  {room.capacity ? (
                    <span className="text-white/35">· {room.capacity}</span>
                  ) : null}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      <p className="mt-2 text-center text-[9px] text-white/30">
        Click a desk to inspect the agent
      </p>
    </div>
  );
}
