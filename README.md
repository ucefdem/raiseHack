# RAISE Hackathon — Multi-Agent Meeting Assistant

Two complementary stacks live in this repo:

1. **Real Google Meet join** (`backend/` + `worker/` + `web/`) — Chrome joins a Meet, virtual audio bridges participants ↔ Gemini Live.
2. **Local speech / agent layer** (`speech/` + `agents/`) — Gradium STT/TTS, wake-word routing, meeting-router, specialist agents.

Long-term goal: wire the speech layer into the Meet worker so agents respond in a real call, not only via `meeting_sim`.

---

## Architecture A — Real Google Meet (Phase 0)

```
Web app (Next.js)  --REST-->  Backend (FastAPI)  --WebSocket-->  Worker (Python)
                                                                    |
                                        Playwright/Chrome + Google Meet
                                                                    |
                                        Virtual audio  <-->  Gemini Live
```

- `backend/` — FastAPI: session REST + `/worker` WebSocket
- `worker/` — Meet control, audio routing, Gemini Live
- `web/` — control panel (paste link, start, status)
- `docs/AUDIO_SETUP.md` — virtual audio (PipeWire / BlackHole)

### Prerequisites

- `GEMINI_API_KEY` with Live API access
- Chrome with agent Google account in `CHROME_USER_DATA_DIR`
- Virtual audio devices (see `docs/AUDIO_SETUP.md`)
- Python 3.11+, Node 18+, PortAudio (`brew install portaudio` on macOS)

### Run Meet stack

```bash
# 1. Backend
cd backend && uv sync && uv run uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Worker (separate terminal)
cd worker && uv sync && uv run playwright install chromium
cp .env.example .env   # edit GEMINI_API_KEY + audio devices
set -a && source .env && set +a
uv run python main.py

# 3. Web app (separate terminal)
cd web && npm install && cp .env.local.example .env.local && npm run dev
```

Open http://localhost:3000 → confirm worker connected → paste Meet link → **Start Agent**.

Verify audio first: `uv run python verify_audio.py devices|speak|listen`

---

## Architecture B — Local speech sim + agents

```
mic → Gradium STT → wake word → meeting-router → specialist → speech-editor → Gradium TTS → speaker
```

Run locally with headphones:

```bash
cd "/Users/niconymand/Documents/RAISE Hackathon"
source venv/bin/activate
pip install -r requirements.txt

export GRADIUM_API_KEY="gd_..."
export BUZZWORDS="Angie,Nikki,Olaf"
export STT_FINAL_SILENCE_S=2.5
export AGENT_INVOKE_DELAY_S=0.5
export STT_TRIGGER_SILENCE_S=1.0

python -m speech.meeting_sim
```

### Agent skills

| Agent | Folder | Wake word |
|-------|--------|-----------|
| Meeting router | `agents/meeting-router/SKILL.md` | — |
| Angie (Orchestrator) | `agents/angie/SKILL.md` | `Angie` |
| Nikki (Sales) | `agents/nikki/SKILL.md` | `Nikki` |
| Olaf (Computer-Use) | `agents/olaf/SKILL.md` | `Olaf` |
| Speech editor | `agents/speech-editor/SKILL.md` | — |

### Speech env vars

| Variable | Default | Description |
|----------|---------|-------------|
| `GRADIUM_API_KEY` | — | STT + TTS |
| `ROUTER_MODE` | `heuristic` | `heuristic` / `listen` / `cloud` |
| `SPEECH_EDITOR_MODE` | `local` | `local` / `cloud` / `off` |
| `BUZZWORDS` | `Angie,Nikki,Olaf` | Wake words |

---

## Project layout

```
backend/          # FastAPI session + worker WebSocket
worker/           # Chrome Meet join + Gemini Live
web/              # Next.js control panel
speech/           # Gradium STT/TTS + routing (local sim)
agents/           # Cursor cloud agent SKILL.md files
docs/             # Audio setup guide
```

## Integration (next step)

Replace Gemini Live in `worker/` with the `speech/` pipeline:

- **Hear**: route `AudioRouter` capture → Gradium STT instead of Gemini input
- **Think**: `AgentRequest` → `OrchestratorClient` (meeting-router + specialists)
- **Speak**: agent reply → Gradium TTS → `AudioRouter` playback into Meet mic

Both stacks already use virtual audio I/O — the swap is in the worker brain, not Chrome.
