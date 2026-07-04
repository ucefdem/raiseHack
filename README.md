# RAISE Hackathon — Multi-Agent Meeting Assistant

Simulate a Google Meet with **mic in / speaker out**, stream real-time transcription, spawn agents on wake words, and speak confirmations via TTS.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Meet Simulator (your laptop mic + speaker)                 │
│  speech/meeting_sim.py                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
         mic (24kHz) ──────┤────── speaker (48kHz)
                           │
              ┌────────────▼────────────┐
              │  Real-time STT (constant)│  ← rolling transcript = meeting context
              │  speech/stt.py           │
              └────────────┬────────────┘
                           │ final utterance
              ┌────────────▼────────────┐
              │  Buzzword trigger        │  "Angie", "Nikki", "Olaf"
              │  speech/triggers.py      │
              └────────────┬────────────┘
                           │ wake word detected
              ┌────────────▼────────────┐
              │  Orchestrator (Angie)    │  ← Cursor Cloud Agent (simulated for now)
              │  speech/orchestrator.py  │
              └────────────┬────────────┘
                           │ "Agent spawned with success"
              ┌────────────▼────────────┐
              │  TTS (Speech Agent)      │
              │  speech/tts.py           │
              └─────────────────────────┘
```

### Agent skills (for Cursor Cloud Agents)

| Agent | Folder | Wake word |
|-------|--------|-----------|
| Angie (Orchestrator) | `agents/angie/SKILL.md` | `Angie` |
| Nikki (Sales / Jira) | `agents/nikki/SKILL.md` | `Nikki` |
| Olaf (Computer-Use) | `agents/olaf/SKILL.md` | `Olaf` |
| Speech (TTS) | `agents/speech/SKILL.md` | — |

## Quick start

```bash
cd "/Users/niconymand/Documents/RAISE Hackathon"
source venv/bin/activate
pip install -r requirements.txt

export GRADIUM_API_KEY="gd_..."
export BUZZWORDS="Angie,Nikki,Olaf"   # optional
export VOICE_ID="YTpq7expH9539ERJ"     # optional — Emma

python -m speech.meeting_sim
```

Put on **headphones**, then say something like:

> "Hey **Angie**, can you get Olaf to show the dashboard?"

Expected output:

```
[14:30:01.123 partial] hey angie can you get olaf
[14:30:03.456 final  ] Hey Angie, can you get Olaf to show the dashboard?
[14:30:03.457] Agent spawned with success — Orchestrator (Angie)
```

You'll also **hear** the confirmation if `SPEAK_CONFIRM=1` (default).

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GRADIUM_API_KEY` | Yes | — | Gradium STT + TTS |
| `VOICE_ID` | No | Emma | TTS voice ID |
| `LANGUAGE` | No | `en` | STT language |
| `BUZZWORDS` | No | `Angie,Nikki,Olaf` | Comma-separated wake words |
| `SPEAK_CONFIRM` | No | `1` | Speak spawn confirmation via TTS |
| `SHOW_PARTIALS` | No | `1` | Live partial lines (`0` = only `[final]` output) |
| `SHOW_PARTIALS` | No | `1` | Print live partial transcript (`0` = finals only) |

## Your scope vs teammates

| Piece | Owner | Status |
|-------|-------|--------|
| Meet sim (mic/speaker) | You | `speech/audio_io.py` |
| Real-time STT + context | You | `speech/stt.py` |
| Buzzword → orchestrator | You | `speech/triggers.py` + `orchestrator.py` |
| Real-time TTS | You | `speech/tts.py` |
| Angie orchestrator (cloud) | Teammate | Simulated → Cloud Agent |
| Nikki / Jira MCP | Teammate | Skill stub ready |
| Olaf computer-use | Teammate | Skill stub ready |
| Real GMeet join (Oleg?) | Future | Out of scope for sim |

## Is real-time possible?

**Yes.** The sim already does:

- **STT**: Gradium WebSocket, ~80 ms frames, partial + final transcripts
- **TTS**: streams PCM chunks to speaker as they're generated
- **Latency**: typically sub-second for STT partials; TTS time-to-first-audio ~200–400 ms

Real GMeet join is a separate integration (browser bot, Meet API, or virtual audio cable). Mic/speaker sim is the right hackathon MVP.

## Project layout

```
speech/
  meeting_sim.py    # ← run this
  audio_io.py       # mic + speaker (Meet sim)
  stt.py            # real-time STT + transcript context
  tts.py            # real-time TTS
  triggers.py       # buzzword detection
  orchestrator.py   # simulated Angie spawn

agents/
  angie/SKILL.md
  nikki/SKILL.md
  olaf/SKILL.md
  speech/SKILL.md
```

## Troubleshooting

- **No `[partial]` lines** → mic permissions (macOS: System Settings → Privacy → Microphone)
- **No `[final]` lines** → pause 1–2 s after speaking (semantic VAD)
- **Wake word not detected** → say the name clearly: "Hey Angie, ..."
- **SSL / certificate error on macOS** → `pip install certifi` (included in requirements) and re-run; or run `/Applications/Python 3.12/Install Certificates.command`
