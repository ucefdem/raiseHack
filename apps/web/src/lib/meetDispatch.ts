/**
 * Fire-and-forget dispatch to the FastAPI backend so the worker joins the
 * shared Meet room whenever a user opens Meet from the 3D building UI.
 *
 * Safe by design: any failure (backend offline, worker not connected, network
 * error) is logged and swallowed — the user still gets the Meet tab.
 */
import { SHARED_MEET_URL } from "@/lib/meetLink";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function dispatchAgentToMeet(
  meetUrl: string = SHARED_MEET_URL,
): Promise<{ sessionId: string | null; started: boolean; error?: string }> {
  try {
    const createRes = await fetch(`${BACKEND_URL}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ meeting_url: meetUrl }),
    });
    if (!createRes.ok) {
      return { sessionId: null, started: false, error: `create ${createRes.status}` };
    }
    const { session_id: sessionId } = (await createRes.json()) as { session_id: string };
    const startRes = await fetch(`${BACKEND_URL}/sessions/${sessionId}/start`, {
      method: "POST",
    });
    return { sessionId, started: startRes.ok, error: startRes.ok ? undefined : `start ${startRes.status}` };
  } catch (err) {
    console.warn("dispatchAgentToMeet failed", err);
    return { sessionId: null, started: false, error: String(err) };
  }
}
