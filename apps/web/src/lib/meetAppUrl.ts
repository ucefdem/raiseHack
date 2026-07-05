import type { VoiceAgentId } from "@raisehack/shared";

/** In-app route to the Meet deploy screen (`/meet`). */
export function meetAppUrl(options?: {
  url?: string;
  agent?: string;
  voiceAgent?: VoiceAgentId;
  room?: string;
  department?: string;
}): string {
  const params = new URLSearchParams();
  if (options?.url) params.set("url", options.url);
  if (options?.agent) params.set("agent", options.agent);
  if (options?.voiceAgent) params.set("voiceAgent", options.voiceAgent);
  if (options?.room) params.set("room", options.room);
  if (options?.department) params.set("department", options.department);
  const qs = params.toString();
  return `/meet${qs ? `?${qs}` : ""}`;
}
