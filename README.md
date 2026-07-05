# RAISE Hackathon — AI Office Platform

3D office UI + multi-agent Google Meet assistant.

## Architecture

```
apps/web  (Next.js + R3F 3D UI)   ─┐
apps/api  (Hono REST stubs)       ─┼─►  backend/ (FastAPI)  ──WS──►  worker/ (Python)
web/      (Meet control panel)    ─┘                                    │
                                                       Playwright/Chrome + Google Meet
                                                                        │
                                                        Virtual audio ⇄ Gradium STT/TTS / agents
```

- `apps/web` — 3D building UI (React Three Fiber)
- `apps/api` — Hono REST stubs (chat, presence, meet)
- `packages/shared` — Shared TypeScript contracts
- `web/` — Meet control panel (Next.js)
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
# 1. Backend
cd backend && uv sync && uv run uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Worker (separate terminal)
cd worker && uv sync && uv run playwright install chromium
cp .env.example .env
set -a && source .env && set +a
uv run python main.py

# 3. Meet control panel
cd web && npm install && cp .env.local.example .env.local && npm run dev

# 4. 3D UI
cd apps/web && npm install && npm run dev
```

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
| Angie (Orchestrator) | `agents/angie/SKILL.md` | `Angie` |
| Nikki (Sales) | `agents/nikki/SKILL.md` | `Nikki` |
| Olaf (Computer-Use) | `agents/olaf/SKILL.md` | `Olaf` |
| Speech editor | `agents/speech-editor/SKILL.md` | — |

## Speech pipeline

```
Meet participants → virtual capture (16 kHz)
  → resample → Gradium STT → wake word → meeting-router
  → Cursor Cloud Agent (tool call with try/except)
  → TTS → resample → virtual mic (24 kHz) → Meet
```

Core loop: `speech/meeting_session.py` · Meet audio bridge: `worker/speech_bridge.py`
