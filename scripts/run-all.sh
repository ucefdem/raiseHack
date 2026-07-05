#!/usr/bin/env bash
# End-to-end dev runner: 3D UI + Hono API + FastAPI backend + speech worker.
# Requires: npm, uv (or python3.11+ venv), and (for full voice loop) Gradium key + BlackHole.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${SHARED_MEET_URL:=https://meet.google.com/lookup/raisehack-office}"
: "${CURSOR_AGENTS_REPOSITORY:=https://github.com/sokolegg/raiseHack}"
: "${ROUTER_MODE:=cloud}"        # cloud → uses Cursor Agents API tool call
: "${OLAF_MODE:=stub}"           # keep stub locally until BlackHole+Meet auth are ready
export SHARED_MEET_URL CURSOR_AGENTS_REPOSITORY ROUTER_MODE OLAF_MODE
export NEXT_PUBLIC_SHARED_MEET_URL="$SHARED_MEET_URL"
export NEXT_PUBLIC_BACKEND_URL="${NEXT_PUBLIC_BACKEND_URL:-http://localhost:8000}"

log_dir="$ROOT/.logs"
mkdir -p "$log_dir"

# Load worker secrets from worker/.env (GRADIUM_API_KEY, etc.)
if [ -f "$ROOT/worker/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/worker/.env"
  set +a
fi

start() {
  local name="$1" cmd="$2"
  echo ">> $name"
  ( eval "$cmd" ) >"$log_dir/$name.log" 2>&1 &
  echo "$!" > "$log_dir/$name.pid"
}

stop_all() {
  for pidfile in "$log_dir"/*.pid; do
    [ -f "$pidfile" ] || continue
    kill "$(cat "$pidfile")" 2>/dev/null || true
    rm -f "$pidfile"
  done
}
trap stop_all EXIT INT TERM

start backend       "cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000"
start hono-api      "cd apps/api && PORT=3001 npm run dev"
start web-3d        "cd apps/web && PORT=3000 npm run dev"

if [ -n "${GRADIUM_API_KEY:-}" ] && [ "${GRADIUM_API_KEY}" != "gd_your_key_here" ]; then
  echo ">> worker (live — Gradium key found)"
else
  echo ">> worker (standby — no Gradium key; UI works, Meet join is simulated)"
fi
start worker "cd worker && uv run python main.py"

echo ""
echo "Backend    → http://localhost:8000/health   (logs: .logs/backend.log)"
echo "Hono API   → http://localhost:3001/health   (logs: .logs/hono-api.log)"
echo "3D UI      → http://localhost:3000          (logs: .logs/web-3d.log)"
echo "Meet URL   → $SHARED_MEET_URL"
echo "Ctrl+C to stop."
wait
