"use client";

import { useEffect, useState } from "react";
import {
  CalendarDays,
  Check,
  CircleDot,
  LayoutGrid,
  Target,
  Users,
  Video,
  X,
} from "lucide-react";
import type { DepartmentPlanItem } from "@raisehack/shared";
import { getAgentsByDepartment } from "@/data/agents";
import { getMeetingRoomsForDepartment } from "@/data/meetingRooms";
import { useSelection } from "@/features/selection/SelectionProvider";
import { FloorSchematic2D } from "./FloorSchematic2D";

type MissionView = "overview" | "plan2d";

function PlanStatusIcon({ status }: { status: DepartmentPlanItem["status"] }) {
  if (status === "done") return <Check className="h-3.5 w-3.5 text-emerald-400" />;
  if (status === "in-progress")
    return <CircleDot className="h-3.5 w-3.5 text-amber-400" />;
  return <CalendarDays className="h-3.5 w-3.5 text-white/35" />;
}

/** Popup shown when a floor/department is clicked (without picking an agent) */
export function DepartmentMissionModal() {
  const { selectedDepartment, selectedAgent, clearSelection } = useSelection();
  const [visible, setVisible] = useState(false);
  const [view, setView] = useState<MissionView>("overview");

  const open = Boolean(selectedDepartment && !selectedAgent);

  useEffect(() => {
    if (open) {
      setView("overview");
      requestAnimationFrame(() => setVisible(true));
    } else {
      setVisible(false);
    }
  }, [open, selectedDepartment?.id]);

  if (!open || !selectedDepartment) return null;

  const accent = selectedDepartment.zone.color ?? "#4ade80";
  const plan = selectedDepartment.missionPlan;
  const agents = getAgentsByDepartment(selectedDepartment.id);
  const rooms = getMeetingRoomsForDepartment(selectedDepartment.id);

  return (
    <div
      className={`fixed inset-0 z-40 flex items-center justify-center transition-opacity duration-300 ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      {/* Backdrop */}
      <button
        type="button"
        aria-label="Close department overview"
        onClick={clearSelection}
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="dept-mission-title"
        className={`relative flex max-h-[min(640px,calc(100vh-5rem))] w-[min(520px,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#101a14]/90 shadow-2xl shadow-black/50 backdrop-blur-2xl transition-transform duration-300 ${
          visible ? "translate-y-0" : "translate-y-4"
        }`}
      >
        {/* Header */}
        <div
          className="flex items-start justify-between gap-4 border-b border-white/8 p-6"
          style={{ background: `linear-gradient(135deg, ${accent}22, transparent 60%)` }}
        >
          <div>
            <p
              className="text-[10px] font-semibold uppercase tracking-[0.2em]"
              style={{ color: accent }}
            >
              Floor {selectedDepartment.floor}
            </p>
            <h2
              id="dept-mission-title"
              className="mt-1 text-2xl font-light tracking-tight text-white"
            >
              {selectedDepartment.name}
            </h2>
            <p className="mt-1 text-sm text-white/50">
              {selectedDepartment.description}
            </p>
          </div>
          <button
            type="button"
            onClick={clearSelection}
            aria-label="Close"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white/40 transition hover:bg-white/10 hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* View toggle */}
        <div className="flex gap-1 border-b border-white/8 p-2">
          <button
            type="button"
            onClick={() => setView("overview")}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
              view === "overview"
                ? "bg-white/12 text-white"
                : "text-white/45 hover:text-white/70"
            }`}
          >
            <Target className="h-3.5 w-3.5" />
            Overview
          </button>
          <button
            type="button"
            onClick={() => setView("plan2d")}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
              view === "plan2d"
                ? "bg-white/12 text-white"
                : "text-white/45 hover:text-white/70"
            }`}
          >
            <LayoutGrid className="h-3.5 w-3.5" />
            2D floor plan
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto p-6">
          {view === "plan2d" ? (
            <FloorSchematic2D department={selectedDepartment} />
          ) : plan ? (
            <>
              {/* Mission */}
              <section>
                <div className="flex items-center gap-2 text-white/45">
                  <Target className="h-3.5 w-3.5" />
                  <p className="text-[10px] font-semibold uppercase tracking-widest">
                    Mission
                  </p>
                </div>
                <p className="mt-2 text-base leading-relaxed text-white/90">
                  {plan.mission}
                </p>
              </section>

              {/* Goals */}
              <section>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-white/45">
                  Goals
                </p>
                <ul className="mt-2 space-y-2">
                  {plan.goals.map((goal) => (
                    <li
                      key={goal}
                      className="flex items-start gap-2.5 rounded-lg border border-white/8 bg-white/5 px-3 py-2.5 text-sm text-white/75"
                    >
                      <span
                        className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
                        style={{ background: accent }}
                      />
                      {goal}
                    </li>
                  ))}
                </ul>
              </section>

              {/* Calendar */}
              <section>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-white/45">
                  Upcoming
                </p>
                <ul className="mt-2 space-y-1.5">
                  {plan.calendar.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition hover:bg-white/5"
                    >
                      <PlanStatusIcon status={item.status} />
                      <span className="flex-1 text-white/75">{item.title}</span>
                      {item.date && (
                        <span className="text-xs tabular-nums text-white/40">
                          {item.date}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            </>
          ) : (
            <p className="text-sm text-white/45">No mission plan published yet.</p>
          )}

          {/* Team */}
          {view === "overview" && (
          <section>
            <div className="flex items-center gap-2 text-white/45">
              <Users className="h-3.5 w-3.5" />
              <p className="text-[10px] font-semibold uppercase tracking-widest">
                Team ({agents.length})
              </p>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {agents.map((agent) => (
                <span
                  key={agent.id}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/70"
                >
                  {agent.name}
                  {agent.error?.needsReview && (
                    <span className="ml-1.5 text-red-400">!</span>
                  )}
                </span>
              ))}
            </div>
          </section>
          )}

          {/* Meeting rooms */}
          {view === "overview" && rooms.length > 0 && (
            <section>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-white/45">
                Meeting rooms
              </p>
              <ul className="mt-2 space-y-1.5">
                {rooms.map((room) => (
                  <li
                    key={room.id}
                    className="flex items-center justify-between gap-3 rounded-lg border border-white/8 bg-white/5 px-3 py-2"
                  >
                    <span className="text-sm text-white/70">{room.name}</span>
                    <a
                      href={room.meetUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-medium text-slate-900 transition hover:opacity-90"
                      style={{ background: accent }}
                    >
                      <Video className="h-3 w-3" />
                      Join
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        {/* Footer */}
        {selectedDepartment.meetUrl && (
          <div className="border-t border-white/8 px-6 py-4">
            <a
              href={selectedDepartment.meetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:opacity-90"
              style={{ background: accent }}
            >
              <Video className="h-4 w-4" />
              Join {selectedDepartment.name} room
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
