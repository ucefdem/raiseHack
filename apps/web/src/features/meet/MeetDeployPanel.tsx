"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SHARED_MEET_URL } from "@/lib/meetLink";
import {
  MEET_STATUS_STYLES,
  normalizeMeetUrl,
  prettifyMeetStatus,
  type MeetSession,
} from "@/lib/meetDeploy";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "/api/backend";

export function MeetDeployPanel() {
  const searchParams = useSearchParams();
  const agentName = searchParams.get("agent");
  const initialUrl = searchParams.get("url") ?? SHARED_MEET_URL;

  const [meetingUrl, setMeetingUrl] = useState(initialUrl);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<MeetSession | null>(null);
  const [workerOnline, setWorkerOnline] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setMeetingUrl(initialUrl);
  }, [initialUrl]);

  const refreshWorker = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND}/worker`);
      if (!res.ok) {
        setWorkerOnline(false);
        return;
      }
      const data = await res.json();
      setWorkerOnline(Boolean(data.online));
    } catch {
      setWorkerOnline(false);
    }
  }, []);

  useEffect(() => {
    refreshWorker();
    const id = setInterval(refreshWorker, 2000);
    return () => clearInterval(id);
  }, [refreshWorker]);

  useEffect(() => {
    if (!sessionId) return;
    const poll = async () => {
      try {
        const res = await fetch(`${BACKEND}/sessions/${sessionId}`);
        if (res.ok) setSession(await res.json());
      } catch {
        /* keep polling */
      }
    };
    poll();
    pollRef.current = setInterval(poll, 1000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [sessionId]);

  const startAgent = async () => {
    setError(null);
    setBusy(true);
    try {
      const createRes = await fetch(`${BACKEND}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meeting_url: normalizeMeetUrl(meetingUrl) }),
      });
      if (!createRes.ok) throw new Error("Failed to create session");
      const created = await createRes.json();
      setSessionId(created.session_id);

      const startRes = await fetch(`${BACKEND}/sessions/${created.session_id}/start`, {
        method: "POST",
      });
      if (!startRes.ok) {
        const detail = await startRes.json().catch(() => ({}));
        throw new Error(
          detail.detail === "worker offline" ? "Worker is offline" : "Failed to start agent",
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  const currentStatus = session?.status ?? "created";
  const canStart = workerOnline && meetingUrl.trim().length > 0 && !busy;

  return (
    <main className="min-h-screen overflow-y-auto bg-slate-950">
      <div className="mx-auto flex max-w-2xl flex-col justify-center px-6 py-16">
        <Link
          href="/"
          className="mb-8 inline-flex text-sm text-slate-400 transition hover:text-slate-200"
        >
          ← Back to office
        </Link>

        <header className="mb-10">
          <p className="mb-2 text-sm font-medium uppercase tracking-widest text-sky-400">
            Meeting Computer Agent
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-white">
            {agentName ? `Deploy ${agentName} to Meet` : "An AI teammate with its own computer."}
          </h1>
          <p className="mt-3 text-slate-400">
            {agentName
              ? `Send ${agentName} into the meeting to listen and respond.`
              : "Paste a Google Meet link and the agent will join, listen, and speak."}
          </p>
        </header>

        <section className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-2xl backdrop-blur">
          <div className="mb-5 flex items-center gap-2">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                workerOnline ? "bg-emerald-400" : "bg-slate-500"
              }`}
            />
            <span className="text-sm text-slate-300">
              Worker {workerOnline ? "connected" : "offline"}
            </span>
          </div>

          <label className="mb-2 block text-sm font-medium text-slate-300">
            Google Meet link
          </label>
          <input
            value={meetingUrl}
            onChange={(e) => setMeetingUrl(e.target.value)}
            placeholder="https://meet.google.com/xxx-yyyy-zzz"
            className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-4 py-3 text-slate-100 outline-none ring-sky-500/40 placeholder:text-slate-500 focus:ring-2"
          />

          <button
            type="button"
            onClick={startAgent}
            disabled={!canStart}
            className="mt-4 w-full rounded-lg bg-sky-500 px-4 py-3 font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
          >
            {busy ? "Starting..." : "Start Agent"}
          </button>

          {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}

          {session && (
            <div className="mt-6 rounded-xl border border-white/10 bg-slate-950/40 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Status</span>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ring-1 ${
                    MEET_STATUS_STYLES[currentStatus] ?? MEET_STATUS_STYLES.created
                  }`}
                >
                  {prettifyMeetStatus(currentStatus)}
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-300">{session.last_event}</p>
              <p className="mt-2 font-mono text-xs text-slate-500">{session.session_id}</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
