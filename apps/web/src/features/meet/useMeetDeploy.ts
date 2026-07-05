"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { VoiceAgentId } from "@raisehack/shared";
import { normalizeMeetUrl, type MeetSession } from "@/lib/meetDeploy";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "/api/backend";

export interface UseMeetDeployOptions {
  initialMeetingUrl: string;
  voiceAgentId?: VoiceAgentId | null;
}

export function useMeetDeploy({ initialMeetingUrl, voiceAgentId }: UseMeetDeployOptions) {
  const [meetingUrl, setMeetingUrl] = useState(initialMeetingUrl);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<MeetSession | null>(null);
  const [workerOnline, setWorkerOnline] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setMeetingUrl(initialMeetingUrl);
  }, [initialMeetingUrl]);

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
        body: JSON.stringify({
          meeting_url: normalizeMeetUrl(meetingUrl),
          voice_agent_id: voiceAgentId ?? null,
        }),
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

  const canStart = workerOnline && meetingUrl.trim().length > 0 && !busy;

  return {
    meetingUrl,
    setMeetingUrl,
    session,
    workerOnline,
    error,
    busy,
    canStart,
    startAgent,
  };
}
