"""Suppress agent triggers while TTS is playing (avoids mic feedback loop)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class AgentGuard:
    """Ignore wake words and optionally mic→STT while the agent speaks."""

    min_deaf_s: float = 6.0
    _deaf_until: float = field(default=0.0, repr=False)

    def arm_for_response(self, text: str) -> None:
        """Block triggers while TTS plays and echo fades (~12 chars/sec + buffer)."""
        est_play_s = len(text) / 12.0 + 2.5
        until = time.monotonic() + max(est_play_s, self.min_deaf_s)
        self._deaf_until = max(self._deaf_until, until)

    def extend(self, seconds: float) -> None:
        self._deaf_until = max(self._deaf_until, time.monotonic() + seconds)

    def is_deaf(self) -> bool:
        return time.monotonic() < self._deaf_until

    def clear(self) -> None:
        """User barge-in — listen again immediately."""
        self._deaf_until = 0.0
