"""Real-time Gradium STT over WebSocket — constant meeting transcription."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import sys
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import websockets

from speech.ssl_context import websocket_ssl_context

logger = logging.getLogger(__name__)

STT_WS_URL = "wss://api.gradium.ai/api/speech/asr"
VAD_THRESHOLD = 0.75
DEBOUNCE_S = 1.5
MIN_FINAL_CHARS = 15
PARTIAL_MAX_LEN = 90
PARTIAL_MIN_INTERVAL_S = 0.35


def _final_text_silence_s() -> float:
    raw = os.getenv("STT_FINAL_SILENCE_S", "5").strip()
    try:
        return max(float(raw), 1.0)
    except ValueError:
        return 5.0


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def _join_segments(segments: list[str]) -> str:
    """Join Gradium text chunks with spaces where needed."""
    if not segments:
        return ""
    result = segments[0]
    for seg in segments[1:]:
        if not seg:
            continue
        prev = result[-1] if result else ""
        nxt = seg[0]
        needs_space = (
            prev
            and nxt
            and not prev.isspace()
            and not nxt.isspace()
            and (prev.isalnum() or prev in ",.!?;:")
            and (nxt.isalnum() or nxt.isalpha())
        )
        if needs_space:
            result += " "
        result += seg
    return result


async def _call_final_handler(
    handler: Callable[[str, TranscriptContext], Awaitable[None] | None] | None,
    text: str,
    context: TranscriptContext,
) -> None:
    if not handler:
        return
    result = handler(text, context)
    if asyncio.iscoroutine(result):
        await result


def _looks_incomplete(text: str) -> bool:
    """Mid-sentence VAD split — hold and merge with the next final."""
    t = text.strip()
    if not t or t[-1] in ".?!":
        return False
    return len(t) < 80


def _format_partial(text: str) -> str:
    if len(text) <= PARTIAL_MAX_LEN:
        return text
    return text[: PARTIAL_MAX_LEN - 3] + "..."


@dataclass
class _PartialPrinter:
    """Rate-limited partial transcript display (works when ANSI \\r does not)."""

    enabled: bool = True
    _last_line: str = ""
    _last_print_at: float = 0.0

    @classmethod
    def from_env(cls) -> _PartialPrinter:
        import os

        show = os.getenv("SHOW_PARTIALS", "1").strip().lower() not in {"0", "false", "no"}
        return cls(enabled=show)

    def show(self, text: str) -> None:
        if not self.enabled or not text:
            return
        line = _format_partial(text)
        now = time.monotonic()
        if line == self._last_line:
            return
        if now - self._last_print_at < PARTIAL_MIN_INTERVAL_S:
            return
        self._last_line = line
        self._last_print_at = now
        # Cursor/IDE terminals often ignore \\r overwrites — emit one line, throttled.
        sys.stdout.write(f"[partial] {line}\n")
        sys.stdout.flush()

    def reset(self) -> None:
        self._last_line = ""


def _print_final(text: str) -> None:
    sys.stdout.write(f"[{_ts()} final  ] {text}\n")
    sys.stdout.flush()


@dataclass
class TranscriptContext:
    """Rolling meeting transcript — serves as context for agents."""

    max_utterances: int = 20
    _utterances: deque[str] = field(default_factory=lambda: deque(maxlen=20))

    def add(self, text: str) -> None:
        self._utterances.append(text)

    def as_text(self) -> str:
        return "\n".join(self._utterances)

    def recent(self, n: int = 5) -> str:
        items = list(self._utterances)[-n:]
        return "\n".join(items)


@dataclass
class GradiumSTT:
    api_key: str
    language: str = "en"
    ws_url: str = STT_WS_URL
    context: TranscriptContext = field(default_factory=TranscriptContext)

    _ws: websockets.WebSocketClientProtocol | None = field(default=None, repr=False)
    _partial_text: str = field(default="", repr=False)
    _segment_texts: list[str] = field(default_factory=list, repr=False)
    _last_final_at: float = field(default=0.0, repr=False)
    _flush_id: int = field(default=0, repr=False)
    _pending_flush: asyncio.Future | None = field(default=None, repr=False)
    _user_speaking: bool = field(default=False, repr=False)
    _partial_printer: _PartialPrinter = field(default_factory=_PartialPrinter.from_env, repr=False)
    _held_utterance: str = field(default="", repr=False)
    _last_text_at: float = field(default=0.0, repr=False)

    async def connect(self) -> None:
        try:
            self._ws = await websockets.connect(
                self.ws_url,
                additional_headers={"x-api-key": self.api_key},
                open_timeout=15,
                ssl=websocket_ssl_context(),
            )
        except Exception as exc:
            raise RuntimeError(f"Gradium STT connection failed: {exc}") from exc

        setup = {
            "type": "setup",
            "model_name": "default",
            "input_format": "pcm",
            "json_config": {"language": self.language},
            "close_ws_on_eos": False,
        }
        await self._ws.send(json.dumps(setup))
        ready = json.loads(await self._ws.recv())
        if ready.get("type") != "ready":
            msg = ready.get("message", ready)
            raise RuntimeError(f"Gradium STT setup failed: {msg}")
        logger.info("[%s] STT live (sample_rate=%s)", _ts(), ready.get("sample_rate"))

    async def run_sender(self, audio_queue: asyncio.Queue[bytes]) -> None:
        assert self._ws is not None
        while True:
            pcm = await audio_queue.get()
            await self._ws.send(
                json.dumps({
                    "type": "audio",
                    "audio": base64.b64encode(pcm).decode("ascii"),
                })
            )

    async def run_receiver(
        self,
        on_partial: Callable[[str, float], None] | None = None,
        on_final: Callable[[str, TranscriptContext], Awaitable[None] | None] | None = None,
        on_speech_start: Callable[[], None] | None = None,
    ) -> None:
        assert self._ws is not None
        while True:
            try:
                raw = await self._ws.recv()
            except websockets.ConnectionClosed as exc:
                raise RuntimeError(f"Gradium STT connection lost: {exc}") from exc

            msg = json.loads(raw)
            mtype = msg.get("type")

            if mtype == "text":
                text = msg.get("text", "")
                if text:
                    self._segment_texts.append(text)
                    self._partial_text = _join_segments(self._segment_texts)
                    self._last_text_at = time.monotonic()
                    if not self._user_speaking:
                        self._user_speaking = True
                        if on_speech_start:
                            on_speech_start()
                    if on_partial:
                        on_partial(self._partial_text, self._last_text_at)
                    self._partial_printer.show(self._partial_text)

            elif mtype == "step":
                vad = msg.get("vad") or []
                if len(vad) >= 3:
                    inactivity = vad[2].get("inactivity_prob", 0.0)
                    silent_long_enough = (
                        self._last_text_at > 0
                        and (time.monotonic() - self._last_text_at) >= _final_text_silence_s()
                    )
                    if (
                        inactivity > VAD_THRESHOLD
                        and self._partial_text.strip()
                        and silent_long_enough
                    ):
                        await self._emit_final(on_final)

            elif mtype == "flushed":
                if self._pending_flush and not self._pending_flush.done():
                    self._pending_flush.set_result(True)

            elif mtype == "error":
                raise RuntimeError(f"Gradium STT error: {msg.get('message')}")

    async def _emit_final(
        self,
        on_final: Callable[[str, TranscriptContext], Awaitable[None] | None] | None,
    ) -> None:
        now = time.monotonic()
        if now - self._last_final_at < DEBOUNCE_S:
            return

        text = self._partial_text.strip()
        if len(text) < MIN_FINAL_CHARS:
            return

        self._last_final_at = now

        self._flush_id += 1
        loop = asyncio.get_running_loop()
        self._pending_flush = loop.create_future()
        assert self._ws is not None
        await self._ws.send(json.dumps({"type": "flush", "flush_id": self._flush_id}))
        try:
            await asyncio.wait_for(self._pending_flush, timeout=2.0)
        except asyncio.TimeoutError:
            pass

        final_text = self._partial_text.strip()
        self._partial_text = ""
        self._segment_texts.clear()
        self._user_speaking = False

        if self._held_utterance:
            final_text = f"{self._held_utterance} {final_text}".strip()
            self._held_utterance = ""

        if _looks_incomplete(final_text):
            self._held_utterance = final_text
            logger.debug("Holding incomplete utterance: %r", final_text[:60])
            return

        self.context.add(final_text)
        self._partial_printer.reset()
        _print_final(final_text)
        # Don't block STT recv while orchestrator / TTS run
        asyncio.create_task(_call_final_handler(on_final, final_text, self.context))
