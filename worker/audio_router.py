"""Audio routing between Google Meet and the Gradium speech pipeline.

Capture side: reads what Chrome/Meet plays out (remote participants) from the
virtual capture device, as 16 kHz mono 16-bit PCM.

Playback side: plays Gradium TTS (resampled to 24 kHz) into the virtual mic
device that Chrome/Meet uses as its microphone.

We deliberately capture only the remote participants (Chrome output), so the
agent's own voice is not looped back into Gemini (PRD section 18).
"""

from __future__ import annotations

import asyncio
import logging
import queue
from typing import AsyncIterator, Optional

import sounddevice as sd

from config import config

logger = logging.getLogger("worker.audio")


def find_device(name: str, kind: str) -> Optional[int]:
    """Resolve a device index by (partial) name. kind is 'input' or 'output'."""
    if not name:
        return None
    want_input = kind == "input"
    for idx, dev in enumerate(sd.query_devices()):
        channels = dev["max_input_channels"] if want_input else dev["max_output_channels"]
        if channels > 0 and name.lower() in dev["name"].lower():
            logger.info("resolved %s device '%s' -> index %d (%s)", kind, name, idx, dev["name"])
            return idx
    logger.warning("could not resolve %s device '%s'; using system default", kind, name)
    return None


class AudioRouter:
    """Full-duplex audio bridge built on sounddevice callback streams."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._capture_q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=100)
        self._playback_q: "queue.Queue[bytes]" = queue.Queue()
        self._playback_buffer = bytearray()
        self._input_stream: sd.RawInputStream | None = None
        self._output_stream: sd.RawOutputStream | None = None
        self._speaking = False

    @property
    def speaking(self) -> bool:
        return self._speaking

    def _on_capture(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            logger.debug("capture status: %s", status)
        if self._loop is None:
            return
        data = bytes(indata)
        try:
            self._loop.call_soon_threadsafe(self._capture_q.put_nowait, data)
        except asyncio.QueueFull:
            pass  # drop if consumer is behind; keeps latency bounded

    def _on_playback(self, outdata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            logger.debug("playback status: %s", status)
        needed = frames * 2  # 16-bit mono
        while len(self._playback_buffer) < needed:
            try:
                self._playback_buffer.extend(self._playback_q.get_nowait())
            except queue.Empty:
                break
        if len(self._playback_buffer) >= needed:
            outdata[:needed] = self._playback_buffer[:needed]
            del self._playback_buffer[:needed]
            self._speaking = True
        else:
            have = len(self._playback_buffer)
            outdata[:have] = self._playback_buffer[:]
            outdata[have:needed] = b"\x00" * (needed - have)
            del self._playback_buffer[:]
            self._speaking = False

    def start(self) -> None:
        self._loop = asyncio.get_running_loop()

        self._input_stream = sd.RawInputStream(
            samplerate=config.input_sample_rate,
            blocksize=config.input_chunk_frames,
            device=find_device(config.capture_device, "input"),
            channels=config.channels,
            dtype="int16",
            callback=self._on_capture,
        )
        self._output_stream = sd.RawOutputStream(
            samplerate=config.output_sample_rate,
            blocksize=0,
            device=find_device(config.playback_device, "output"),
            channels=config.channels,
            dtype="int16",
            callback=self._on_playback,
        )
        self._input_stream.start()
        self._output_stream.start()
        logger.info("audio router started")

    def stop(self) -> None:
        for stream in (self._input_stream, self._output_stream):
            if stream is not None:
                stream.stop()
                stream.close()
        self._input_stream = None
        self._output_stream = None
        logger.info("audio router stopped")

    async def capture_chunks(self) -> AsyncIterator[bytes]:
        """Yield 16 kHz mono PCM chunks captured from the meeting."""
        while True:
            yield await self._capture_q.get()

    def play(self, pcm: bytes) -> None:
        """Queue 24 kHz mono PCM to be played into the meeting microphone."""
        self._playback_q.put(pcm)

    def clear_playback(self) -> None:
        """Drop any pending audio (used on barge-in / interruption)."""
        with self._playback_q.mutex:
            self._playback_q.queue.clear()
        self._playback_buffer.clear()
