"""Wait for silence after a final before invoking an agent."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from speech.agent_context import AgentRequest, AgentResponse
    from speech.stt import TranscriptContext

logger = logging.getLogger(__name__)

DEFAULT_DELAY_S = 2.0


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


@dataclass
class AgentInvokeScheduler:
    """
    Agent calls happen only after:
      1. A [final] transcript (never on [partial])
      2. A wake word in that final
      3. No new finals and no new speech for `delay_s` seconds
    """

    delay_s: float = DEFAULT_DELAY_S
    _generation: int = field(default=0, repr=False)
    _task: asyncio.Task | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> AgentInvokeScheduler:
        raw = os.getenv("AGENT_INVOKE_DELAY_S", str(DEFAULT_DELAY_S)).strip()
        try:
            delay = float(raw)
        except ValueError:
            delay = DEFAULT_DELAY_S
        return cls(delay_s=max(delay, 0.5))

    def on_new_final(self) -> None:
        """Any new final means the user may still be talking — reset the wait."""
        self._generation += 1
        self.cancel()

    def on_speech_resume(self) -> None:
        """User started speaking again before we invoked — cancel."""
        self._generation += 1
        self.cancel()

    def cancel(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    def schedule(
        self,
        mentioned: list[str],
        utterance: str,
        context: TranscriptContext,
        invoke: Callable[[AgentRequest], Awaitable[AgentResponse]],
    ) -> None:
        self.cancel()
        my_gen = self._generation
        primary = mentioned[-1] if mentioned else ""

        async def _wait_and_invoke() -> None:
            try:
                words = ", ".join(mentioned)
                print(
                    f"[{_ts()}] Wake word(s) [{words}] in final — "
                    f"waiting {self.delay_s:.1f}s, then consulting meeting-router..."
                )
                await asyncio.sleep(self.delay_s)
                if my_gen != self._generation:
                    return
                from speech.agent_context import AgentRequest

                request = AgentRequest(
                    wake_word=primary,
                    mentioned_wake_words=mentioned,
                    utterance=utterance,
                    meeting_transcript=context.as_text(),
                    recent_transcript=context.recent(8),
                )
                await invoke(request)
            except asyncio.CancelledError:
                pass

        self._task = asyncio.create_task(_wait_and_invoke())
