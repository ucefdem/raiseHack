"""Wake-word detection — presence only; orchestrator decides intent."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field


@dataclass
class BuzzwordTrigger:
    """
    Detect wake-word mentions in finalized speech.

    Intentional vs casual distinction is left to the orchestrator LLM.
    """

    buzzwords: list[str]
    cooldown_s: float = 8.0
    _last_fired: float = field(default=0.0, repr=False)

    @classmethod
    def from_env(cls, raw: str | None, cooldown_s: float = 8.0) -> BuzzwordTrigger:
        if not raw:
            words = ["angie", "nikki", "olaf"]
        else:
            words = [w.strip().lower() for w in raw.split(",") if w.strip()]
        return cls(buzzwords=words, cooldown_s=cooldown_s)

    def mentions(self, text: str) -> list[str]:
        """Wake words found in text, ordered by last occurrence (most recent last)."""
        lowered = text.lower()
        hits: list[tuple[int, str]] = []
        for word in self.buzzwords:
            for match in re.finditer(rf"\b{re.escape(word)}\b", lowered):
                hits.append((match.start(), word))
        hits.sort(key=lambda item: item[0])
        seen: set[str] = set()
        ordered: list[str] = []
        for _, word in hits:
            if word in seen:
                continue
            seen.add(word)
            ordered.append(word)
        return ordered

    def try_fire(self) -> bool:
        """Record a trigger if cooldown has passed."""
        now = time.monotonic()
        if now - self._last_fired < self.cooldown_s:
            return False
        self._last_fired = now
        return True

    def scan(self, text: str) -> list[str] | None:
        """
        Return mentioned wake words if any appear and cooldown has passed.

        Returns None when no wake words or still in cooldown.
        """
        mentioned = self.mentions(text)
        if not mentioned:
            return None
        if not self.try_fire():
            return None
        return mentioned
