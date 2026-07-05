/**
 * Shared Google Meet room — every agent in the 3D office dials the same link.
 *
 * Precedence (build-time):
 *   1. NEXT_PUBLIC_SHARED_MEET_URL (env)
 *   2. Fallback constant below (safe demo default)
 */
export const SHARED_MEET_URL: string =
  process.env.NEXT_PUBLIC_SHARED_MEET_URL ??
  "https://meet.google.com/lookup/raisehack-office";
