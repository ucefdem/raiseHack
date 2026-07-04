"""Microphone capture and speaker playback — simulates a Meet audio channel."""

from __future__ import annotations

import asyncio
import logging
import threading

import numpy as np

logger = logging.getLogger(__name__)

STT_SAMPLE_RATE = 24000
STT_FRAME_SAMPLES = 1920  # 80 ms at 24 kHz
TTS_SAMPLE_RATE = 48000


def _import_sounddevice():
    try:
        import sounddevice as sd

        return sd
    except ImportError:
        raise RuntimeError("Install sounddevice: pip install sounddevice")


class RingBuffer:
    """Thread-safe byte buffer for streaming PCM16 playback."""

    def __init__(self, max_bytes: int = TTS_SAMPLE_RATE * 2 * 10):
        self._buf = bytearray(max_bytes)
        self._max = max_bytes
        self._read = 0
        self._write = 0
        self._size = 0
        self._lock = threading.Lock()

    def write(self, data: bytes) -> None:
        if not data:
            return
        with self._lock:
            for b in data:
                if self._size >= self._max:
                    self._read = (self._read + 1) % self._max
                    self._size -= 1
                self._buf[self._write] = b
                self._write = (self._write + 1) % self._max
                self._size += 1

    def read(self, nbytes: int) -> bytes:
        with self._lock:
            n = min(nbytes, self._size)
            out = bytearray(n)
            for i in range(n):
                out[i] = self._buf[self._read]
                self._read = (self._read + 1) % self._max
                self._size -= 1
            return bytes(out)

    def clear(self) -> None:
        with self._lock:
            self._read = self._write = self._size = 0

    @property
    def size(self) -> int:
        with self._lock:
            return self._size


class AudioPlayer:
    def __init__(self, sample_rate: int = TTS_SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.buffer = RingBuffer()
        self._stream = None
        self._sd = _import_sounddevice()

    def _callback(self, outdata, frames, _time_info, status):
        if status:
            logger.warning("Playback status: %s", status)
        needed = frames * 2
        chunk = self.buffer.read(needed)
        if len(chunk) < needed:
            chunk += b"\x00" * (needed - len(chunk))
        outdata[:] = np.frombuffer(chunk, dtype=np.int16).reshape(-1, 1)

    def start(self) -> None:
        if self._stream is not None:
            return
        self._stream = self._sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=self._callback,
            blocksize=3840,
        )
        self._stream.start()
        logger.debug("Speaker ready (%d Hz)", self.sample_rate)

    def enqueue(self, pcm_bytes: bytes) -> None:
        self.buffer.write(pcm_bytes)

    def barge_in(self) -> None:
        self.buffer.clear()

    def busy(self) -> bool:
        return self.buffer.size > 0

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None


class MicCapture:
    """Streams mic PCM16 frames into an asyncio queue."""

    def __init__(
        self,
        queue: asyncio.Queue[bytes],
        sample_rate: int = STT_SAMPLE_RATE,
        frame_samples: int = STT_FRAME_SAMPLES,
    ):
        self.queue = queue
        self.sample_rate = sample_rate
        self.frame_samples = frame_samples
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stream = None
        self._sd = _import_sounddevice()

    def _callback(self, indata, _frames, _time_info, status):
        if status:
            logger.warning("Capture status: %s", status)
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._enqueue, bytes(indata))

    def _enqueue(self, pcm: bytes) -> None:
        try:
            self.queue.put_nowait(pcm)
        except asyncio.QueueFull:
            pass

    async def run(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._stream = self._sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.frame_samples,
            callback=self._callback,
        )
        self._stream.start()
        logger.debug("Microphone ready (%d Hz)", self.sample_rate)
        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            if self._stream:
                self._stream.stop()
                self._stream.close()
