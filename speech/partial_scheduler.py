"""Fast agent path — trigger on stable partial + short silence (skip [final] wait)."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Awaitable, Callable

from speech.router_heuristic import is_direct_agent_call

if TYPE_CHECKING:
    from speech.agent_context import AgentRequest, AgentResponse
    from speech.stt import TranscriptContext
    from speech.triggers import BuzzwordTrigger

DEFAULT_TRIGGER_SILENCE_S = 1.0


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def _trigger_silence_s() -> float:
    raw = os.getenv("STT_TRIGGER_SILENCE_S", str(DEFAULT_TRIGGER_SILENCE_S)).strip()
    try:
        return max(float(raw), 0.4)
    except ValueError:
        return DEFAULT_TRIGGER_SILENCE_S


def partial_trigger_enabled() -> bool:
    return os.getenv("STT_PARTIAL_TRIGGER", "1").strip().lower() not in {"0", "false", "no"}


@dataclass
class PartialTriggerScheduler:
    """
    Fire the router when a partial shows a direct agent ask and text goes quiet.

    Much faster than waiting for [final] + STT_FINAL_SILENCE_S on long utterances.
    """

    trigger_silence_s: float = DEFAULT_TRIGGER_SILENCE_S
    _generation: int = field(default=0, repr=False)
    _task: asyncio.Task | None = field(default=None, repr=False)
    _pending_text: str = field(default="", repr=False)
    _pending_last_text_at: float = field(default=0.0, repr=False)

    @classmethod
    def from_env(cls) -> PartialTriggerScheduler:
        return cls(trigger_silence_s=_trigger_silence_s())

    def on_speech_resume(self) -> None:
        self._generation += 1
        self.cancel()

    def cancel(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    def on_partial(
        self,
        text: str,
        last_text_at: float,
        context: TranscriptContext,
        triggers: BuzzwordTrigger,
        invoke: Callable[[AgentRequest], Awaitable[AgentResponse]],
    ) -> None:
        if not partial_trigger_enabled():
            return

        mentioned = triggers.mentions(text)
        if not mentioned:
            return

        direct, _ = is_direct_agent_call(text, mentioned)
        if not direct:
            return

        self.cancel()
        self._pending_text = text
        self._pending_last_text_at = last_text_at
        my_gen = self._generation

        async def _wait_and_invoke() -> None:
            try:
                await asyncio.sleep(self.trigger_silence_s)
                if my_gen != self._generation:
                    return
                if self._pending_text != text:
                    return
                if time.monotonic() - self._pending_last_text_at < self.trigger_silence_s:
                    return

                if not triggers.try_fire():
                    return

                primary = mentioned[-1]
                words = ", ".join(mentioned)
                print(
                    f"[{_ts()}] Direct ask [{words}] in partial — "
                    f"consulting meeting-router (no [final] wait)..."
                )

                from speech.agent_context import AgentRequest

                request = AgentRequest(
                    wake_word=primary,
                    mentioned_wake_words=mentioned,
                    utterance=text,
                    meeting_transcript=context.as_text(),
                    recent_transcript=context.recent(8),
                )
                await invoke(request)
            except asyncio.CancelledError:
                pass

        self._task = asyncio.create_task(_wait_and_invoke())
