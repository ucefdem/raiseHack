"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { SHARED_MEET_URL } from "@/lib/meetLink";
import type { VoiceAgentId } from "@raisehack/shared";
import { MeetDeployContent } from "./MeetDeployContent";

export function MeetDeployPanel() {
  const searchParams = useSearchParams();
  const agentName = searchParams.get("agent");
  const voiceAgentParam = searchParams.get("voiceAgent") as VoiceAgentId | null;
  const initialUrl = searchParams.get("url") ?? SHARED_MEET_URL;

  return (
    <main className="min-h-screen overflow-y-auto bg-slate-950">
      <div className="mx-auto flex max-w-2xl flex-col justify-center px-6 py-16">
        <Link
          href="/"
          className="mb-8 inline-flex text-sm text-slate-400 transition hover:text-slate-200"
        >
          ← Back to office
        </Link>

        <section className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-2xl backdrop-blur">
          <MeetDeployContent
            initialMeetingUrl={initialUrl}
            agentName={agentName}
            voiceAgentId={voiceAgentParam}
          />
        </section>
      </div>
    </main>
  );
}
