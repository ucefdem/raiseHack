"""Gemini Live speech-to-speech client.

Uses the google-genai SDK Live API for a bidirectional audio session. We rely
on the Live API's built-in automatic VAD and proactive audio so the agent
decides when to respond (PRD FR-0.8 / FR-0.9) instead of a custom VAD pipeline.

Audio contract: send 16 kHz mono 16-bit PCM, receive 24 kHz mono 16-bit PCM.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Awaitable, Callable

from google import genai
from google.genai import types

from config import config

logger = logging.getLogger("worker.gemini")

SYSTEM_INSTRUCTION = (
    "You are an AI teammate participating in a live meeting by voice. "
    "You are helpful, concise, and meeting-friendly, and you do not over-talk. "
    "Wait for a pause before speaking and never interrupt people. "
    "Only respond when someone is clearly addressing you or asking the group for help; "
    "otherwise stay quiet and keep listening. "
    "Keep responses short and spoken-friendly. Briefly confirm what you are doing. "
    "Do not claim to have completed an action unless it actually happened."
)

AudioCallback = Callable[[bytes], None]
StateCallback = Callable[[str], Awaitable[None]]
InterruptCallback = Callable[[], None]


def _build_config() -> types.LiveConnectConfig:
    kwargs: dict = {
        "response_modalities": ["AUDIO"],
        "system_instruction": SYSTEM_INSTRUCTION,
        "speech_config": types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=config.gemini_voice)
            )
        ),
        "output_audio_transcription": types.AudioTranscriptionConfig(),
        "input_audio_transcription": types.AudioTranscriptionConfig(),
    }
    # Proactive audio lets the model choose when to reply, but it is only a valid
    # setup field on v1alpha native-audio models. Opt-in via GEMINI_PROACTIVE_AUDIO.
    if config.gemini_proactive_audio:
        kwargs["proactivity"] = types.ProactivityConfig(proactive_audio=True)
    return types.LiveConnectConfig(**kwargs)


class GeminiLiveClient:
    def __init__(
        self,
        on_audio: AudioCallback,
        on_state: StateCallback,
        on_interrupt: InterruptCallback,
    ) -> None:
        if not config.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        http_options = (
            {"api_version": config.gemini_api_version} if config.gemini_api_version else None
        )
        self._client = genai.Client(
            api_key=config.gemini_api_key,
            http_options=http_options,
        )
        self._on_audio = on_audio
        self._on_state = on_state
        self._on_interrupt = on_interrupt

    async def run(self, capture_iter: AsyncIterator[bytes]) -> None:
        logger.info("connecting to Gemini Live model=%s", config.gemini_model)
        async with self._client.aio.live.connect(
            model=config.gemini_model, config=_build_config()
        ) as session:
            await self._on_state("listening")
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._send_loop(session, capture_iter))
                tg.create_task(self._receive_loop(session))

    async def _send_loop(self, session, capture_iter: AsyncIterator[bytes]) -> None:  # noqa: ANN001
        mime = f"audio/pcm;rate={config.input_sample_rate}"
        async for chunk in capture_iter:
            await session.send_realtime_input(audio=types.Blob(data=chunk, mime_type=mime))

    async def _receive_loop(self, session) -> None:  # noqa: ANN001
        while True:
            async for response in session.receive():
                server_content = getattr(response, "server_content", None)

                if server_content is not None and getattr(server_content, "interrupted", False):
                    logger.info("interrupted by speaker (barge-in)")
                    self._on_interrupt()
                    await self._on_state("listening")
                    continue

                if response.data:
                    await self._on_state("speaking")
                    self._on_audio(response.data)

                if server_content is not None and getattr(server_content, "turn_complete", False):
                    await self._on_state("listening")
