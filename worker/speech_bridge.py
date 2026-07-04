"""Bridge worker AudioRouter ↔ Gradium speech pipeline."""

from __future__ import annotations

import asyncio
import logging

from audio_router import AudioRouter
from config import config

from speech.audio_io import STT_FRAME_SAMPLES
from speech.audio_output import AudioOutput
from speech.guard import AgentGuard
from speech.resample import resample_pcm16

logger = logging.getLogger("worker.speech_bridge")

# Gradium TTS PCM matches local AudioPlayer default
TTS_SAMPLE_RATE = 48000


class MeetAudioOutput:
    """Play TTS into the Meet virtual microphone via AudioRouter."""

    def __init__(
        self,
        router: AudioRouter,
        playback_rate: int = config.output_sample_rate,
        tts_rate: int = TTS_SAMPLE_RATE,
    ) -> None:
        self._router = router
        self._playback_rate = playback_rate
        self._tts_rate = tts_rate

    def start(self) -> None:
        pass

    def enqueue(self, pcm_bytes: bytes) -> None:
        if self._playback_rate != self._tts_rate:
            pcm_bytes = resample_pcm16(pcm_bytes, self._tts_rate, self._playback_rate)
        self._router.play(pcm_bytes)

    def barge_in(self) -> None:
        self._router.clear_playback()

    def busy(self) -> bool:
        return self._router.speaking

    def stop(self) -> None:
        self._router.clear_playback()


async def meet_capture_to_stt(
    router: AudioRouter,
    stt_queue: asyncio.Queue[bytes],
    guard: AgentGuard,
) -> None:
    """Read Meet capture, resample to Gradium STT rate, respect guard deaf window."""
    capture_rate = config.input_sample_rate
    stt_rate = int(config.stt_sample_rate)
    pending = bytearray()
    frame_bytes = STT_FRAME_SAMPLES * 2

    async for chunk in router.capture_chunks():
        if guard.is_deaf():
            pending.clear()
            continue

        pcm = resample_pcm16(chunk, capture_rate, stt_rate)
        pending.extend(pcm)

        while len(pending) >= frame_bytes:
            frame = bytes(pending[:frame_bytes])
            del pending[:frame_bytes]
            try:
                stt_queue.put_nowait(frame)
            except asyncio.QueueFull:
                pass
