"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Share2, User, Video, X } from "lucide-react";
import type { Agent } from "@raisehack/shared";
import { getAgentsByDepartment } from "@/data/agents";
import { getActivityByAgentId } from "@/data/agentActivities";
import { useAgentTracking } from "@/features/scene/AgentTrackingProvider";
import { useSelection } from "@/features/selection/SelectionProvider";
import { FloorPlanPreview } from "@/features/departments/FloorPlanPreview";
import { getVoiceAgent, getAngieSubagents } from "@/data/voiceAgents";
import { meetAppUrl } from "@/lib/meetAppUrl";

type PanelTab = "overview" | "structure" | "activity";

const statusLabel: Record<Agent["status"], string> = {
  online: "Available",
  busy: "Heads down",
  offline: "Away",
};

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

function clampPanelPosition(
  anchorX: number,
  anchorY: number,
  panelW: number,
  panelH: number,
): { left: number; top: number } {
  const margin = 16;
  const headerClearance = 72;
  const offsetX = 36;
  const offsetY = -panelH * 0.15;

  let left = anchorX + offsetX;
  let top = anchorY + offsetY;

  if (left + panelW > window.innerWidth - margin) {
    left = anchorX - panelW - offsetX;
  }

  left = Math.max(margin, Math.min(left, window.innerWidth - panelW - margin));
  top = Math.max(
    headerClearance,
    Math.min(top, window.innerHeight - panelH - margin),
  );

  return { left, top };
}

export function AgentDetailModal() {
  const { selectedAgent, selectedDepartment, clearSelection } = useSelection();
  const { screenAnchorRef } = useAgentTracking();
  const [tab, setTab] = useState<PanelTab>("activity");
  const [visible, setVisible] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedAgent) {
      setTab("activity");
      requestAnimationFrame(() => setVisible(true));
    } else {
      setVisible(false);
    }
  }, [selectedAgent?.id]);

  useEffect(() => {
    if (!selectedAgent) return;

    let frame = 0;
    const tick = () => {
      const panel = panelRef.current;
      const anchor = screenAnchorRef.current;
      if (panel && anchor) {
        const { width, height } = panel.getBoundingClientRect();
        const { left, top } = clampPanelPosition(anchor.x, anchor.y, width, height);
        panel.style.left = `${left}px`;
        panel.style.top = `${top}px`;
      }
      frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [selectedAgent?.id, screenAnchorRef, tab]);

  if (!selectedAgent || !selectedDepartment) return null;

  const activity = getActivityByAgentId(selectedAgent.id);
  const departmentAgents = getAgentsByDepartment(selectedDepartment.id);
  const accent = selectedDepartment.zone.color ?? "#4ade80";
  const voiceAgent = selectedAgent.voiceAgentId
    ? getVoiceAgent(selectedAgent.voiceAgentId)
    : null;

  const close = () => clearSelection();

  const panelStyle: React.CSSProperties = {
    maxHeight: "calc(100vh - 7rem)",
    left: 0,
    top: 0,
  };

  return (
    <div
      ref={panelRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="agent-panel-title"
      className={`pointer-events-auto fixed z-30 flex w-[min(360px,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-2xl border border-white/10 bg-black/45 shadow-2xl shadow-black/40 backdrop-blur-2xl transition-opacity duration-300 ease-out ${
        visible ? "opacity-100" : "opacity-0"
      }`}
      style={panelStyle}
    >
      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/8 p-2">
        <TabButton active={tab === "overview"} onClick={() => setTab("overview")}>
          Overview
        </TabButton>
        <TabButton active={tab === "structure"} onClick={() => setTab("structure")}>
          Structure
        </TabButton>
        <TabButton active={tab === "activity"} onClick={() => setTab("activity")}>
          Activity
        </TabButton>
      </div>

      <div className="flex flex-1 flex-col overflow-y-auto p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2
              id="agent-panel-title"
              className="text-xl font-light tracking-tight text-white"
            >
              {selectedAgent.name}
            </h2>
            <p className="mt-1 text-sm text-white/50">
              {selectedDepartment.name} · Floor {selectedDepartment.floor}
            </p>
            <p className="text-xs capitalize text-white/35">
              {selectedAgent.role} · {statusLabel[selectedAgent.status]}
            </p>
          </div>
          <button
            type="button"
            onClick={close}
            aria-label="Close"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white/35 transition hover:bg-white/8 hover:text-white/70"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {selectedAgent.error?.needsReview && (
          <section className="mt-4 flex gap-3 rounded-xl border border-red-500/40 bg-red-500/10 p-4">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-red-300">
                Needs human review
              </p>
              <p className="mt-1 text-sm leading-relaxed text-red-100/90">
                {selectedAgent.error.message}
              </p>
            </div>
          </section>
        )}

        {tab === "overview" && (
          <div className="mt-4 space-y-4">
            <section className="rounded-xl border border-white/8 bg-white/5 p-4">
              <div className="flex items-center gap-2 text-white/45">
                <User className="h-3.5 w-3.5" />
                <p className="text-[10px] uppercase tracking-wider">Created by</p>
              </div>
              <p className="mt-2 text-sm font-medium text-white/85">
                {selectedAgent.createdBy.name}
              </p>
              <p className="text-xs text-white/45">
                {selectedAgent.createdBy.role}
                {selectedAgent.createdBy.team ? ` · ${selectedAgent.createdBy.team}` : ""}
              </p>
            </section>

            <p className="text-sm leading-relaxed text-white/50">
              {selectedDepartment.description}
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-white/8 bg-white/5 p-3">
                <p className="text-[10px] uppercase tracking-wider text-white/35">
                  Teammates
                </p>
                <p className="mt-1 text-2xl font-light text-white">
                  {departmentAgents.length}
                </p>
              </div>
              <div className="rounded-xl border border-white/8 bg-white/5 p-3">
                <p className="text-[10px] uppercase tracking-wider text-white/35">
                  Online now
                </p>
                <p className="mt-1 text-2xl font-light" style={{ color: accent }}>
                  {departmentAgents.filter((a) => a.status === "online").length}
                </p>
              </div>
            </div>
          </div>
        )}

        {tab === "structure" && (
          <div className="mt-4 space-y-4">
            <FloorPlanPreview department={selectedDepartment} />
            <div className="flex items-center justify-between rounded-xl border border-white/8 bg-white/5 px-4 py-3">
              <span className="text-xs text-white/45">Total area</span>
              <span className="text-sm font-medium text-white/80">
                {(departmentAgents.length * 42.8).toFixed(1)} sq.m
              </span>
            </div>
          </div>
        )}

        {tab === "activity" && (
          <div className="mt-4 space-y-4">
            <section
              className="relative overflow-hidden rounded-xl border p-4"
              style={{ borderColor: `${accent}33`, background: `${accent}0d` }}
            >
              <p className="text-[10px] font-semibold uppercase tracking-widest text-white/40">
                Right now
              </p>
              <p className="mt-2 text-base leading-relaxed text-white/90">
                {activity?.task ?? "No activity logged"}
              </p>
            </section>

            {activity && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-white/8 bg-white/5 p-3">
                    <p className="text-[10px] uppercase tracking-wider text-white/35">
                      Location
                    </p>
                    <p className="mt-1 text-sm text-white/70">{activity.location}</p>
                  </div>
                  <div className="rounded-xl border border-white/8 bg-white/5 p-3">
                    <p className="text-[10px] uppercase tracking-wider text-white/35">
                      Mood
                    </p>
                    <p className="mt-1 text-sm text-white/70">{activity.mood}</p>
                  </div>
                </div>
                {activity.progress !== undefined && (
                  <section>
                    <div className="flex justify-between text-xs text-white/45">
                      <span>Task progress</span>
                      <span>{activity.progress}%</span>
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${activity.progress}%`, background: accent }}
                      />
                    </div>
                  </section>
                )}
              </>
            )}

            <section className="rounded-xl border border-white/8 bg-white/5 p-4">
              <p className="text-[10px] uppercase tracking-wider text-white/35">
                Persona
              </p>
              <p className="mt-2 text-sm leading-relaxed text-white/55">
                {selectedAgent.personaPrompt}
              </p>
            </section>

            {voiceAgent && (
              <section
                className="rounded-xl border p-4"
                style={{ borderColor: `${accent}33`, background: `${accent}0d` }}
              >
                <p className="text-[10px] font-semibold uppercase tracking-widest text-white/40">
                  Voice agent
                </p>
                <p className="mt-2 text-sm font-medium text-white/85">
                  {voiceAgent.title} · wake word &ldquo;{voiceAgent.wakeWord}&rdquo;
                </p>
                <p className="mt-1 text-xs leading-relaxed text-white/50">
                  {voiceAgent.description}
                </p>
                {voiceAgent.id === "angie" && (
                  <div className="mt-3 space-y-2 border-t border-white/8 pt-3">
                    <p className="text-[10px] uppercase tracking-wider text-white/35">
                      Subagents
                    </p>
                    {getAngieSubagents().map((sub) => (
                      <div key={sub.id} className="rounded-lg border border-white/8 bg-black/20 px-3 py-2">
                        <p className="text-xs font-medium text-white/75">
                          {sub.name} · {sub.title}
                        </p>
                        <p className="mt-0.5 text-[11px] leading-relaxed text-white/45">
                          {sub.description}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
                <p className="mt-2 font-mono text-[10px] text-white/35">
                  {voiceAgent.skillPath}
                </p>
              </section>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between gap-3 border-t border-white/8 px-5 py-4">
        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] text-white/55">
          Floor {selectedDepartment.floor}
        </div>
        <div className="flex items-center gap-2">
          {selectedAgent.meetUrl && (
            <Link
              href={meetAppUrl({
                url: selectedAgent.meetUrl,
                agent: selectedAgent.name,
                voiceAgent: selectedAgent.voiceAgentId,
              })}
              className="flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-medium text-slate-900 transition hover:opacity-90"
              style={{ background: accent }}
            >
              <Video className="h-3.5 w-3.5" />
              Meet
            </Link>
          )}
          <button
            type="button"
            title="Share"
            className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/45 transition hover:bg-white/10 hover:text-white"
          >
            <Share2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
