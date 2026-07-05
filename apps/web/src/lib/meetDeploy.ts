export type MeetSession = {
  session_id: string;
  status: string;
  last_event: string;
  worker_status: string;
};

export const MEET_STATUS_STYLES: Record<string, string> = {
  created: "bg-slate-500/20 text-slate-300 ring-slate-500/40",
  joining_meeting: "bg-amber-500/20 text-amber-300 ring-amber-500/40",
  in_waiting_room: "bg-amber-500/20 text-amber-300 ring-amber-500/40",
  in_meeting: "bg-emerald-500/20 text-emerald-300 ring-emerald-500/40",
  listening: "bg-emerald-500/20 text-emerald-300 ring-emerald-500/40",
  thinking: "bg-violet-500/20 text-violet-300 ring-violet-500/40",
  speaking: "bg-fuchsia-500/20 text-fuchsia-300 ring-fuchsia-500/40",
  error: "bg-rose-500/20 text-rose-300 ring-rose-500/40",
};

export function prettifyMeetStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function normalizeMeetUrl(raw: string): string {
  const url = raw.trim();
  if (!url) return url;
  if (/^https?:\/\//i.test(url)) return url;
  return `https://${url.replace(/^\/+/, "")}`;
}
