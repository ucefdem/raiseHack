---
name: speech-agent
description: >-
  Speech agent. Converts agent text output into natural spoken audio via Gradium
  TTS. Use for all agent responses that should be heard in the meeting.
---

# Speech Agent

Translates LLM/agent text output into natural speech for the simulated Meet.

## Implementation

Lives in `speech/tts.py` — Gradium TTS WebSocket, persistent connection, 48 kHz PCM.

## Pipeline

```
wake word in [final] → AgentRequest → orchestrator.invoke() → AgentResponse.text → TTS
```

## AgentRequest (speech → orchestrator)

Defined in `speech/agent_context.py`. Passed on every spawn:

| Field | Purpose |
|-------|---------|
| `wake_word` | Which agent was called (`nikki`, `olaf`, `angie`) |
| `utterance` | The triggering final transcript |
| `meeting_transcript` | Full rolling meeting text |
| `recent_transcript` | Last ~8 finals (compact context) |

Angie replaces `OrchestratorClient.invoke()` — speech layer unchanged.

## Configuration

| Env var | Default | Purpose |
|---------|---------|---------|
| `VOICE_ID` | `YTpq7expH9539ERJ` | Gradium voice |
| `SPEAK_RESPONSE` | `1` | Speak `AgentResponse.text` via TTS |

## Guidelines for upstream agents

- Keep responses under 3 sentences (meeting attention span)
- No markdown, bullets, or URLs spelled out unless needed
- Numbers and dates should be speech-friendly

## Barge-in

If the user starts speaking during TTS playback, audio is interrupted automatically.
