"use client";

import { useEffect, useState } from "react";
import { Users, Video, X } from "lucide-react";
import { getDepartmentById } from "@/data/departments";
import { useSelection } from "@/features/selection/SelectionProvider";

export function MeetingRoomModal() {
  const { selectedMeetingRoom, clearSelection } = useSelection();
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
      className={`fixed inset-0 z-40 flex items-center justify-center transition-opacity duration-300 ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      <button
        type="button"
        aria-label="Close meeting room"
        onClick={clearSelection}
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="meeting-room-title"
        className={`relative w-[min(440px,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-white/10 bg-[#101a14]/92 shadow-2xl shadow-black/50 backdrop-blur-2xl transition-transform duration-300 ${
          visible ? "translate-y-0" : "translate-y-4"
        }`}
      >
        <div
          className="border-b border-white/8 p-6"
          style={{ background: `linear-gradient(135deg, ${accent}28, transparent 65%)` }}
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p
                className="text-[10px] font-semibold uppercase tracking-[0.2em]"
                style={{ color: accent }}
              >
                Meeting room · Floor {selectedMeetingRoom.floor}
              </p>
              <h2
                id="meeting-room-title"
                className="mt-1 text-xl font-light text-white"
              >
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

        <div className="space-y-5 p-6">
          <section>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-white/45">
              Cross-department access
            </p>
            <p className="mt-1 text-sm text-white/55">
              Agents and people from these departments can join this room:
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
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

          <section className="rounded-xl border border-white/8 bg-white/5 p-4">
            <p className="text-[10px] uppercase tracking-wider text-white/35">
              Use this room for
            </p>
            <p className="mt-2 text-sm leading-relaxed text-white/70">
              {selectedMeetingRoom.departmentIds.length > 1
                ? "Cross-team syncs, incident response, and mixed human + agent sessions."
                : "Team standups and focused department sessions."}
            </p>
          </section>
        </div>

        <div className="border-t border-white/8 px-6 py-4">
          <a
            href={selectedMeetingRoom.meetUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-medium text-slate-900 transition hover:opacity-90"
            style={{ background: accent }}
          >
            <Video className="h-4 w-4" />
            Join {selectedMeetingRoom.name}
          </a>
        </div>
      </div>
    </div>
  );
}
