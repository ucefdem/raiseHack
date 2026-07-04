# RAISE Hackathon — Multi-Agent Meeting Assistant

Google Meet agent: paste a link in the web app, worker joins via Chrome, hears the call with Gradium STT, routes wake words to agents, speaks back with TTS.

## Architecture

```
Web app (Next.js)  --REST-->  Backend (FastAPI)  --WebSocket-->  Worker (Python)
                                                                    |
                                        Playwright/Chrome + Google Meet
                                                                    |
                                        Virtual audio  <-->  Gradium STT / TTS / agents
```

- `backend/` — FastAPI: session REST + `/worker` WebSocket
- `worker/` — Meet control, audio routing, speech pipeline (`speech/meeting_session.py`)
- `web/` — control panel (paste link, start, status)
- `speech/` — Gradium STT/TTS, wake-word routing, orchestrator (used by worker)
- `agents/` — Cursor cloud agent `SKILL.md` files
- `docs/AUDIO_SETUP.md` — virtual audio (PipeWire / BlackHole)

### Prerequisites

- `GRADIUM_API_KEY` for STT + TTS
- Chrome with agent Google account in `CHROME_USER_DATA_DIR`
- Virtual audio devices (see `docs/AUDIO_SETUP.md`)
- Python 3.11+, Node 18+, PortAudio (`brew install portaudio` on macOS)

### Run

```bash
# 1. Backend
cd backend && uv sync && uv run uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Worker (separate terminal)
cd worker && uv sync && uv run playwright install chromium
cp .env.example .env
# Edit .env: GRADIUM_API_KEY, CAPTURE_DEVICE, PLAYBACK_DEVICE
set -a && source .env && set +a
uv run python main.py

# 3. Web app (separate terminal)
cd web && npm install && cp .env.local.example .env.local && npm run dev
```

Open http://localhost:3000 → confirm worker connected → paste Meet link → **Start Agent**.

Verify audio first: `cd worker && uv run python verify_audio.py devices|speak|listen`

### Agent skills

| Agent | Folder | Wake word |
|-------|--------|-----------|
| Meeting router | `agents/meeting-router/SKILL.md` | — |
| Angie (Orchestrator) | `agents/angie/SKILL.md` | `Angie` |
| Nikki (Sales) | `agents/nikki/SKILL.md` | `Nikki` |
| Olaf (Computer-Use) | `agents/olaf/SKILL.md` | `Olaf` |
| Speech editor | `agents/speech-editor/SKILL.md` | — |

### Worker / speech env vars

| Variable | Default | Description |
|----------|---------|-------------|
| `GRADIUM_API_KEY` | — | STT + TTS (in `worker/.env`) |
| `ROUTER_MODE` | `heuristic` | `heuristic` / `listen` / `cloud` |
| `SPEECH_EDITOR_MODE` | `local` | `local` / `cloud` / `off` |
| `BUZZWORDS` | `Angie,Nikki,Olaf` | Wake words |
| `CAPTURE_DEVICE` | — | Virtual input (Meet audio in) |
| `PLAYBACK_DEVICE` | — | Virtual output (agent mic) |

## Project layout

```
backend/          # FastAPI session + worker WebSocket
worker/           # Chrome Meet join + Gradium speech pipeline
web/              # Next.js control panel
speech/           # STT, TTS, routing (imported by worker)
agents/           # Cursor cloud agent SKILL.md files
docs/             # Audio setup guide
```

## Speech pipeline (inside worker)

```
Meet participants → virtual capture (16 kHz)
  → resample → Gradium STT → wake word → meeting-router → TTS
  → resample → virtual mic (24 kHz) → Meet hears agent
```

Core loop: `speech/meeting_session.py` · Meet audio bridge: `worker/speech_bridge.py`
