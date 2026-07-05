"use client";

import type { Department } from "@raisehack/shared";

/** Wireframe isometric floor plan — green campus glow */
export function FloorPlanPreview({ department }: { department: Department }) {
  const accent = department.zone.color ?? "#4ade80";

  return (
    <div className="relative overflow-hidden rounded-xl border border-emerald-400/20 bg-gradient-to-br from-slate-900/80 to-slate-950/90 p-4">
      <div
        className="absolute inset-0 opacity-30"
        style={{
          background: `radial-gradient(circle at 50% 60%, ${accent}55, transparent 70%)`,
        }}
      />
      <svg
        viewBox="0 0 200 160"
        className="relative mx-auto h-36 w-full"
        aria-label={`Floor plan for ${department.name}`}
      >
        {/* Outer walls */}
        <polygon
          points="40,120 100,150 160,120 100,90"
          fill="none"
          stroke={accent}
          strokeWidth="2"
          opacity="0.9"
        />
        <polygon
          points="40,120 40,70 100,40 100,90"
          fill="none"
          stroke={accent}
          strokeWidth="2"
          opacity="0.7"
        />
        <polygon
          points="100,90 100,40 160,70 160,120"
          fill="none"
          stroke={accent}
          strokeWidth="2"
          opacity="0.7"
        />

        {/* Interior rooms */}
        <line x1="100" y1="90" x2="100" y2="120" stroke={accent} strokeWidth="1.5" opacity="0.6" />
        <line x1="70" y1="105" x2="130" y2="105" stroke={accent} strokeWidth="1.5" opacity="0.6" />
        <line x1="70" y1="70" x2="70" y2="105" stroke={accent} strokeWidth="1" opacity="0.4" />
        <line x1="130" y1="70" x2="130" y2="105" stroke={accent} strokeWidth="1" opacity="0.4" />

        {/* Room labels */}
        <text x="78" y="98" fill={accent} fontSize="7" opacity="0.8">
          Agents
        </text>
        <text x="112" y="98" fill={accent} fontSize="7" opacity="0.8">
          Hub
        </text>
        <text x="88" y="132" fill={accent} fontSize="7" opacity="0.8">
          Lounge
        </text>

        {/* Glow nodes */}
        <circle cx="85" cy="95" r="3" fill={accent} opacity="0.9" />
        <circle cx="115" cy="95" r="3" fill={accent} opacity="0.9" />
        <circle cx="100" cy="125" r="3" fill={accent} opacity="0.7" />
      </svg>
      <p className="relative mt-2 text-center text-[10px] uppercase tracking-widest text-emerald-400/70">
        Floor {department.floor} layout
      </p>
    </div>
  );
}
