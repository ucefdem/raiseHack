---
name: speech-agent
description: >-
  Speech delivery agent. Plays Gradium TTS audio in the simulated Meet. Upstream
  text must pass through speech-editor before reaching TTS.
---

# Speech Agent (TTS delivery)

Plays agent replies aloud via Gradium TTS. **Does not** rewrite LLM text — that is `speech-editor`.

## Pipeline

```
wake word → meeting-router → specialist LLM
  → speech-editor (conversational rewrite)
  → AgentResponse.text (spoken script)
  → Gradium TTS (speech/tts.py) → speaker
```

## Implementation

| Piece | Location |
|-------|----------|
| TTS WebSocket | `speech/tts.py` |
| Speech rewrite | `agents/speech-editor/SKILL.md` + `speech/speech_editor.py` |
| Orchestrator hook | `speech/orchestrator.py` → `SpeechEditorClient.prepare()` |

## AgentResponse fields

| Field | Goes to TTS? |
|-------|----------------|
| `text` | **Yes** — post speech-editor |
| `raw_text` | No — original LLM output (logs) |

## Configuration

| Env var | Default | Purpose |
|---------|---------|---------|
| `VOICE_ID` | Emma | Gradium voice |
| `SPEAK_RESPONSE` | `1` | Speak `AgentResponse.text` |
| `SPEECH_EDITOR_MODE` | `local` | `local` / `cloud` / `off` |

## Barge-in

User speech during TTS interrupts playback (`speech/guard.py`).
