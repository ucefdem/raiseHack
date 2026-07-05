/** In-app route to the Meet deploy screen (`/meet`). */
export function meetAppUrl(options?: {
  url?: string;
  agent?: string;
  room?: string;
  department?: string;
}): string {
  const params = new URLSearchParams();
  if (options?.url) params.set("url", options.url);
  if (options?.agent) params.set("agent", options.agent);
  if (options?.room) params.set("room", options.room);
  if (options?.department) params.set("department", options.department);
  const qs = params.toString();
  return `/meet${qs ? `?${qs}` : ""}`;
}
