"""Data contract between the speech layer and orchestrator / cloud agents."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass
class AgentRequest:
    """Everything an agent needs to understand the meeting and the ask."""

    wake_word: str
    """Primary wake-word hint (usually the last mentioned), e.g. nikki."""

    mentioned_wake_words: list[str]
    """All wake words heard in the triggering utterance, in speech order."""

    utterance: str
    """The finalized transcript that triggered the agent (may include the wake word)."""

    meeting_transcript: str
    """Full rolling meeting transcript so far."""

    recent_transcript: str
    """Last few finalized utterances — usually enough for routing + task understanding."""

    triggered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def summary_for_log(self) -> str:
        words = ",".join(self.mentioned_wake_words) or self.wake_word
        return (
            f"wake_words=[{words}] "
            f"utterance={self.utterance[:80]!r} "
            f"transcript_lines={self.meeting_transcript.count(chr(10)) + 1}"
        )


@dataclass
class AgentResponse:
    """Text returned by orchestrator / specialist agent — fed to TTS."""

    text: str
    """Spoken aloud via TTS — after speech-editor, if enabled."""

    agent_name: str
    """Who answered, e.g. Sales Agent (Nikki)."""

    raw_text: str | None = None
    """Pre-edit LLM text from specialist/orchestrator (logs only)."""

    routed_to: str | None = None
    """Optional: specialist Angie delegated to."""

    should_respond: bool = False
    """True only when meeting-router returns action=respond."""

    reason: str | None = None
    """Optional orchestrator rationale (logs only, not spoken)."""

    def summary_for_log(self) -> str:
        preview = self.text if len(self.text) <= 120 else self.text[:117] + "..."
        return f"{self.agent_name}: {preview}"
