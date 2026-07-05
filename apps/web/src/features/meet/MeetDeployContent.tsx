"use client";

import type { VoiceAgentId } from "@raisehack/shared";
import { getVoiceAgent, getAngieSubagents } from "@/data/voiceAgents";
import {
  MEET_STATUS_STYLES,
  prettifyMeetStatus,
} from "@/lib/meetDeploy";
import { useMeetDeploy } from "./useMeetDeploy";

export interface MeetDeployContentProps {
  initialMeetingUrl: string;
  agentName?: string | null;
  voiceAgentId?: VoiceAgentId | null;
  /** Embedded in meeting room panel — tighter layout, no page header */
  compact?: boolean;
  accentColor?: string;
}

export function MeetDeployContent({
  initialMeetingUrl,
  agentName,
  voiceAgentId,
  compact = false,
  accentColor = "#38bdf8",
}: MeetDeployContentProps) {
  const voiceAgent = voiceAgentId ? getVoiceAgent(voiceAgentId) : null;
  const {
    meetingUrl,
    setMeetingUrl,
    session,
    workerOnline,
    error,
    busy,
    canStart,
    startAgent,
  } = useMeetDeploy({ initialMeetingUrl, voiceAgentId });

  const currentStatus = session?.status ?? "created";

  return (
    <div className={compact ? "space-y-4" : "space-y-5"}>
      {compact && agentName && (
        <p className="text-sm text-white/60">
          Deploying{" "}
          <span className="font-medium text-white">{agentName}</span> to this room
        </p>
      )}

      {!compact && (
        <header>
          <p className="mb-2 text-sm font-medium uppercase tracking-widest text-sky-400">
            Meeting Computer Agent
          </p>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            {agentName ? `Deploy ${agentName} to Meet` : "Deploy agent to Meet"}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            {voiceAgent?.id === "angie"
              ? "Angie joins as your meeting manager. She delegates to Nikki (sales) and Olaf (computer-use) when you need specialist work."
              : agentName
                ? `Send ${agentName} into the meeting to listen and respond.`
                : "Paste a Google Meet link and the agent will join, listen, and speak."}
          </p>
        </header>
      )}

      {voiceAgent?.id === "angie" && (
        <div
          className={`rounded-lg border px-4 py-3 ${
            compact ? "border-sky-500/20 bg-sky-500/8" : "border-sky-500/25 bg-sky-500/10"
          }`}
        >
          <p className="text-xs font-medium uppercase tracking-wider text-sky-300">
            Managed by Angie
          </p>
          <p className="mt-1 text-sm text-slate-300">{voiceAgent.description}</p>
          {!compact && (
            <ul className="mt-3 space-y-2">
              {getAngieSubagents().map((sub) => (
                <li key={sub.id} className="text-xs text-slate-400">
                  <span className="font-medium text-slate-300">{sub.name}</span> — {sub.description}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="flex items-center gap-2">
        <span
          className={`inline-block h-2.5 w-2.5 rounded-full ${
            workerOnline ? "bg-emerald-400" : "bg-slate-500"
          }`}
        />
        <span className="text-sm text-white/55">
          Worker {workerOnline ? "connected" : "offline"}
        </span>
      </div>
      {!workerOnline && (
        <p className="text-xs leading-relaxed text-white/40">
          Start the worker in a terminal:{" "}
          <code className="rounded bg-white/5 px-1.5 py-0.5 text-[11px] text-white/55">
            cd worker && uv run python main.py
          </code>
          . Without a Gradium key it runs in standby mode (simulated join).
        </p>
      )}

      <div>
        <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-white/45">
          Google Meet link
        </label>
        <input
          value={meetingUrl}
          onChange={(e) => setMeetingUrl(e.target.value)}
          placeholder="https://meet.google.com/xxx-yyyy-zzz"
          className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2.5 text-sm text-slate-100 outline-none ring-sky-500/40 placeholder:text-slate-500 focus:ring-2"
        />
      </div>

      <button
        type="button"
        onClick={startAgent}
        disabled={!canStart}
        className="w-full rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-900 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        style={{ background: accentColor }}
      >
        {busy ? "Starting..." : "Start Agent"}
      </button>

      {error && <p className="text-sm text-rose-400">{error}</p>}

      {session && (
        <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-white/45">Status</span>
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ring-1 ${
                MEET_STATUS_STYLES[currentStatus] ?? MEET_STATUS_STYLES.created
              }`}
            >
              {prettifyMeetStatus(currentStatus)}
            </span>
          </div>
          <p className="mt-3 text-sm text-white/70">{session.last_event}</p>
          <p className="mt-2 font-mono text-xs text-white/35">{session.session_id}</p>
        </div>
      )}
    </div>
  );
}
