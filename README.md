# Meeting Computer Agent - Phase 0

An AI teammate with its own computer. Phase 0 is the **voice foundation**: paste
a Google Meet link in the web app, and a dedicated worker machine joins the Meet
through a logged-in Chrome profile, hears the conversation, and speaks back
using Gemini Live (waiting for silence before responding).

Trello, file reading, browsing, and screen sharing are later phases and are not
included here.

## Architecture

```
Web app (Next.js)  --REST-->  Backend (FastAPI)  --WebSocket-->  Worker (Python)
                                                                    |
                                        Playwright/Chrome + Google Meet
                                                                    |
                                        Virtual audio  <-->  Gemini Live
```

- `backend/` - FastAPI: session REST endpoints + `/worker` WebSocket, in-memory state.
- `worker/` - Python worker: WebSocket client, Meet control, audio routing, Gemini Live.
- `web/` - Next.js + Tailwind control panel (paste link, start, live status).
- `docs/AUDIO_SETUP.md` - virtual audio setup for Linux (PipeWire) and macOS (BlackHole).

## Prerequisites

- A `GEMINI_API_KEY` with Live API access.
- Google Chrome installed, with an **agent-only** Google account already logged
  into the profile at `CHROME_USER_DATA_DIR`.
- Virtual audio devices configured (see `docs/AUDIO_SETUP.md`).
- Python 3.11+ and Node 18+.
- **PortAudio** system library (required by `sounddevice`):
  - Debian/Ubuntu: `sudo apt-get install libportaudio2`
  - macOS: `brew install portaudio`

## Run it

Python services use [uv](https://docs.astral.sh/uv/) (install with
`curl -LsSf https://astral.sh/uv/install.sh | sh`). `uv sync` creates the
`.venv` and installs from the committed `uv.lock`.

### 1. Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Worker

```bash
cd worker
uv sync
uv run playwright install chromium   # or use your system Chrome via CHROME_CHANNEL=chrome
cp .env.example .env                 # then edit GEMINI_API_KEY and audio devices
set -a && source .env && set +a
uv run python main.py
```

Before running the full worker, verify audio independently (PRD milestones M3/M4):

```bash
uv run python verify_audio.py devices   # list device names
uv run python verify_audio.py speak     # M4: participants hear a test tone
uv run python verify_audio.py listen    # M3: level meter reacts to speech
```

### 3. Web app

```bash
cd web
npm install
cp .env.local.example .env.local   # points at http://localhost:8000
npm run dev
```

Open http://localhost:3000, confirm "Worker connected", paste a Meet link, and
click **Start Agent**.

## Phase 0 done criteria

Paste link -> worker joins the Meet -> someone says "Can you hear me?" -> the
agent waits for silence and answers out loud, then handles a few basic spoken
questions without constantly interrupting.

## Status vocabulary

`worker_offline`, `worker_connected`, `joining_meeting`, `in_waiting_room`,
`in_meeting`, `listening`, `thinking`, `speaking`, `error`.
