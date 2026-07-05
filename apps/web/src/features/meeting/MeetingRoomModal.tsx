"use client";

import { useEffect, useState } from "react";
import { Users, X } from "lucide-react";
import { getDepartmentById } from "@/data/departments";
import { MeetDeployContent } from "@/features/meet/MeetDeployContent";
import { useSelection } from "@/features/selection/SelectionProvider";

export function MeetingRoomModal() {
  const { selectedMeetingRoom, meetDeployAgent, clearSelection } = useSelection();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (selectedMeetingRoom) {
      requestAnimationFrame(() => setVisible(true));
    } else {
      setVisible(false);
    }
  }, [selectedMeetingRoom?.id]);

  if (!selectedMeetingRoom) return null;

  const accent = selectedMeetingRoom.accentColor ?? "#4ade80";
  const departments = selectedMeetingRoom.departmentIds
    .map((id) => getDepartmentById(id))
    .filter(Boolean);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="meeting-room-title"
      className={`pointer-events-none fixed right-6 top-1/2 z-40 w-[min(420px,calc(100vw-2rem))] max-h-[min(640px,90vh)] transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
        visible
          ? "translate-x-0 -translate-y-1/2 scale-100 opacity-100"
          : "translate-x-10 -translate-y-1/2 scale-[0.96] opacity-0"
      }`}
    >
      <div
        className="pointer-events-auto flex max-h-[min(640px,90vh)] flex-col overflow-hidden rounded-2xl border bg-[#101a14]/95 shadow-2xl shadow-black/50"
        style={{
          borderColor: `${accent}44`,
          boxShadow: visible ? `0 24px 48px rgba(0,0,0,0.45), 0 0 0 1px ${accent}22` : undefined,
        }}
      >
        <div
          className="shrink-0 border-b border-white/8 p-5"
          style={{ background: `linear-gradient(135deg, ${accent}32, transparent 65%)` }}
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p
                className="text-[10px] font-semibold uppercase tracking-[0.2em]"
                style={{ color: accent }}
              >
                Meeting room · Floor {selectedMeetingRoom.floor}
              </p>
              <h2 id="meeting-room-title" className="mt-1 text-lg font-light text-white">
                {selectedMeetingRoom.name}
              </h2>
              {selectedMeetingRoom.capacity && (
                <p className="mt-1 flex items-center gap-1.5 text-sm text-white/50">
                  <Users className="h-3.5 w-3.5" />
                  Up to {selectedMeetingRoom.capacity} participants
                </p>
              )}
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
        </div>

        <div className="space-y-5 overflow-y-auto p-5">
          <section>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-white/45">
              Departments in this room
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {departments.map((dept) => (
                <span
                  key={dept!.id}
                  className="rounded-full border px-3 py-1 text-xs font-medium"
                  style={{
                    borderColor: `${dept!.zone.color ?? accent}55`,
                    background: `${dept!.zone.color ?? accent}18`,
                    color: dept!.zone.color ?? accent,
                  }}
                >
                  {dept!.name}
                </span>
              ))}
            </div>
          </section>

          <div className="border-t border-white/8 pt-5">
            <p className="mb-4 text-[10px] font-semibold uppercase tracking-widest text-white/45">
              Deploy to Meet
            </p>
            <MeetDeployContent
              key={`${selectedMeetingRoom.id}-${meetDeployAgent?.id ?? "room"}`}
              initialMeetingUrl={selectedMeetingRoom.meetUrl}
              agentName={meetDeployAgent?.name}
              voiceAgentId={meetDeployAgent?.voiceAgentId ?? "angie"}
              compact
              accentColor={accent}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
