# RAISE Hackathon — AI Office Platform

3D office UI + multi-agent Google Meet assistant.

## Architecture

```
apps/web  (Next.js UI: / + /meet)  ─┐
apps/api  (Hono REST stubs)        ─┼─►  backend/ (FastAPI)  ──WS──►  worker/ (Python)
                                    ─┘                                    │
                                                       Playwright/Chrome + Google Meet
                                                                        │
                                                        Virtual audio ⇄ Gradium STT/TTS / agents
```

- `apps/web` — 3D headquarters (`/`) + Meet deploy screen (`/meet`)
- `apps/api` — Hono REST stubs (chat, presence, meet)
- `packages/shared` — Shared TypeScript contracts
- `backend/` — FastAPI: session REST + `/worker` WebSocket
- `worker/` — Meet control, audio routing, speech pipeline
- `speech/` — Gradium STT/TTS, wake-word routing, orchestrator
- `agents/` — Cursor cloud agent `SKILL.md` files
- `docs/AUDIO_SETUP.md` — virtual audio setup

## Prerequisites

- `GRADIUM_API_KEY` for STT + TTS
- `CURSOR_API_KEY` for cloud agent invocation (see below)
- Chrome with agent Google account in `CHROME_USER_DATA_DIR`
- Virtual audio devices (see `docs/AUDIO_SETUP.md`)
- Python 3.11+, Node 18+, PortAudio (`brew install portaudio` on macOS)

## Run

```bash
# UI (headquarters + /meet deploy screen)
npm install && npm run dev          # http://localhost:3000

# Backend
cd backend && uv sync && uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Worker
cd worker && uv sync && uv run playwright install chromium
cp .env.example .env && uv run python main.py
```

**Flow:** `/` → click agent → info popup → **Meet** → `/meet` → share link + Start Agent

## Shared Meet link

All agents dial the same Meet room via `SHARED_MEET_URL` (see `.env.example`).
Backend exposes it at `GET /meet-url`, worker uses it as the default target,
and `speech/agent_context.py` injects it into every agent invocation.

## Cursor Cloud Agents API

Set `CURSOR_API_KEY` and (optionally) override `CURSOR_AGENTS_API_URL`.
The voice loop dispatches wake-word commands via `speech/cursor_cloud_client.py`,
which wraps the [Cursor Agents REST API](https://docs.cursor.com/en/background-agent/api)
with retry + try/except. Failures never crash the meeting loop.

## Agent skills

| Agent | Folder | Wake word |
|-------|--------|-----------|
| Meeting router | `agents/meeting-router/SKILL.md` | — |
| Angie (Incident orchestrator) | `agents/angie/SKILL.md` | `Angie` |
| Nikki (Code — local mock) | `agents/nikki/SKILL.md` | `Nikki` |
| Olaf (Computer-Use) | `agents/olaf/SKILL.md` | `Olaf` |
| Speech editor | `agents/speech-editor/SKILL.md` | — |

## Speech pipeline

```
Meet audio → Gradium STT → wake word → meeting-router
  → Angie delegates → Nikki (raw incident analysis)
  → speech-editor (conversational script)
  → Gradium TTS → Meet audio
```

Core loop: `speech/meeting_session.py` · Meet audio bridge: `worker/speech_bridge.py`

## Mock incident codebase

Demo customer complaints map to a **local** bug — no Git repo access required.

```
mock-incident/
  INCIDENT.md           # customer write-up
  app/checkout.py       # planted bug (empty cart → KeyError)
  app/checkout_fixed.py # reference fix
```

Nikki reads these files via `speech/nikki_client.py`. Override path with `MOCK_INCIDENT_ROOT` in `worker/.env`.

**Try in local sim:** `ROUTER_MODE=heuristic` then say *"Angie, a customer says checkout crashes on an empty cart."*
