"""Real-time Gradium TTS over WebSocket — natural speech output."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
import websockets

from speech.audio_output import AudioOutput
from speech.ssl_context import websocket_ssl_context

logger = logging.getLogger(__name__)

TTS_WS_URL = "wss://api.gradium.ai/api/speech/tts"


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


@dataclass
class GradiumTTS:
    api_key: str
    voice_id: str
    ws_url: str = TTS_WS_URL

    _ws: websockets.WebSocketClientProtocol | None = field(default=None, repr=False)
    _recv_task: asyncio.Task | None = field(default=None, repr=False)
    _player: AudioOutput | None = field(default=None, repr=False)
    _active_req_id: str | None = field(default=None, repr=False)
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    _ready_futures: dict[str, asyncio.Future] = field(default_factory=dict, repr=False)
    _eos_futures: dict[str, asyncio.Future] = field(default_factory=dict, repr=False)

    async def connect(self) -> None:
        self._ws = await websockets.connect(
            self.ws_url,
            additional_headers={"x-api-key": self.api_key},
            open_timeout=15,
            ssl=websocket_ssl_context(),
        )
        logger.info("[%s] TTS connected", _ts())

    async def _ensure_recv_loop(self, player: AudioOutput) -> None:
        self._player = player
        if self._recv_task is None or self._recv_task.done():
            self._recv_task = asyncio.create_task(self._recv_loop())

    async def _recv_loop(self) -> None:
        assert self._ws is not None
        while True:
            try:
                raw = await self._ws.recv()
            except websockets.ConnectionClosed:
                return

            msg = json.loads(raw)
            mtype = msg.get("type")
            req_id = msg.get("client_req_id")

            if mtype == "ready":
                fut = self._ready_futures.pop(req_id or "_default", None)
                if fut and not fut.done():
                    fut.set_result(True)

            elif mtype == "audio":
                if self._cancel_event.is_set():
                    continue
                if self._player:
                    self._player.enqueue(base64.b64decode(msg["audio"]))

            elif mtype == "end_of_stream":
                if req_id:
                    fut = self._eos_futures.pop(req_id, None)
                    if fut and not fut.done():
                        fut.set_result(True)
                if req_id == self._active_req_id:
                    self._active_req_id = None

            elif mtype == "error":
                raise RuntimeError(msg.get("message", "TTS error"))

    async def speak(self, text: str, player: AudioOutput) -> bool:
        await self._ensure_recv_loop(player)
        assert self._ws is not None

        req_id = f"req-{uuid.uuid4().hex[:8]}"
        self._active_req_id = req_id
        self._cancel_event.clear()

        loop = asyncio.get_running_loop()
        ready_fut = loop.create_future()
        eos_fut = loop.create_future()
        self._ready_futures[req_id] = ready_fut
        self._eos_futures[req_id] = eos_fut

        setup = {
            "type": "setup",
            "voice_id": self.voice_id,
            "model_name": "default",
            "output_format": "pcm",
            "close_ws_on_eos": False,
            "client_req_id": req_id,
        }
        try:
            await self._ws.send(json.dumps(setup))
            await asyncio.wait_for(ready_fut, timeout=10.0)
            if self._cancel_event.is_set():
                return True
            await self._ws.send(json.dumps({"type": "text", "text": text, "client_req_id": req_id}))
            await self._ws.send(json.dumps({"type": "end_of_stream", "client_req_id": req_id}))
            await asyncio.wait_for(eos_fut, timeout=60.0)
            logger.info("[%s] TTS done (%d chars)", _ts(), len(text))
            return True
        except Exception as exc:
            logger.error("[%s] TTS failed: %s", _ts(), exc)
            self._ready_futures.pop(req_id, None)
            self._eos_futures.pop(req_id, None)
            self._active_req_id = None
            return False

    def cancel(self) -> None:
        self._cancel_event.set()
        self._active_req_id = None

    async def run(self, speech_queue: asyncio.Queue[str], player: AudioOutput) -> None:
        player.start()
        while True:
            text = await speech_queue.get()
            ok = await self.speak(text, player)
            if not ok:
                print(f"[TTS failed] {text}")
