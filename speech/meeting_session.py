"""Reusable Gradium STT → router → TTS meeting loop."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from speech.agent_context import AgentRequest
from speech.audio_output import AudioOutput
from speech.guard import AgentGuard
from speech.invoke_scheduler import AgentInvokeScheduler
from speech.orchestrator import OrchestratorClient, router_mode
from speech.partial_scheduler import PartialTriggerScheduler, partial_trigger_enabled
from speech.stt import GradiumSTT, TranscriptContext
from speech.angie_instant_client import (
    AngieInstantClient,
    angie_invoke_delay_s,
    hold_ack_text,
    instant_mode,
    should_instant_ack,
)
from speech.triggers import BuzzwordTrigger
from speech.tts import GradiumTTS

logger = logging.getLogger(__name__)

DEFAULT_VOICE_ID = "YTpq7expH9539ERJ"
StateCallback = Callable[[str, str | None], Awaitable[None]]


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


@dataclass
class SpeechConfig:
    gradium_key: str
    voice_id: str = DEFAULT_VOICE_ID
    language: str = "en"
    buzzwords: str | None = None
    speak_response: bool = True
    active_voice_agent: str | None = None


def speech_config_from_env(
    *,
    buzzwords: str | None = None,
    active_voice_agent: str | None = None,
) -> SpeechConfig:
    key = os.getenv("GRADIUM_API_KEY", "").strip()
    placeholders = {"", "gd_your_key_here", "your_key_here"}
    if key in placeholders:
        raise RuntimeError(
            "GRADIUM_API_KEY is missing or still the .env.example placeholder. "
            "Set your real key in worker/.env."
        )
    env_buzzwords = os.getenv("BUZZWORDS", "").strip() or None
    return SpeechConfig(
        gradium_key=key,
        voice_id=os.getenv("VOICE_ID", DEFAULT_VOICE_ID).strip(),
        language=os.getenv("LANGUAGE", "en").strip(),
        buzzwords=buzzwords if buzzwords is not None else env_buzzwords,
        speak_response=os.getenv("SPEAK_RESPONSE", "1").strip() != "0",
        active_voice_agent=active_voice_agent,
    )


async def wait_playback_done(output: AudioOutput, timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    while not output.busy() and time.monotonic() < deadline:
        await asyncio.sleep(0.05)
    while output.busy() and time.monotonic() < deadline:
        await asyncio.sleep(0.1)
    await asyncio.sleep(0.4)


async def verify_gradium(cfg: SpeechConfig) -> None:
    """Fail fast if Gradium rejects the API key (before joining Meet)."""
    stt = GradiumSTT(api_key=cfg.gradium_key, language=cfg.language)
    try:
        await stt.connect()
    except RuntimeError as exc:
        raise RuntimeError(
            "Gradium API key rejected. Set a valid GRADIUM_API_KEY in worker/.env. "
            f"Detail: {exc}"
        ) from exc
    finally:
        if stt._ws is not None:
            await stt._ws.close()


class MeetingSpeechSession:
    """
    Constant STT + wake-word routing + agent TTS.

    Audio I/O is injected: local mic/speaker (optional local dev) or Meet virtual devices (worker).
    """

    def __init__(
        self,
        cfg: SpeechConfig,
        output: AudioOutput,
        on_state: StateCallback | None = None,
    ) -> None:
        self.cfg = cfg
        self.output = output
        self._on_state = on_state

        self.guard = AgentGuard()
        self.scheduler = AgentInvokeScheduler.from_env()
        self.partial_scheduler = PartialTriggerScheduler.from_env()
        self.stt = GradiumSTT(api_key=cfg.gradium_key, language=cfg.language)
        self.tts = GradiumTTS(api_key=cfg.gradium_key, voice_id=cfg.voice_id)
        self.orchestrator = OrchestratorClient(active_voice_agent=cfg.active_voice_agent)
        self.angie_instant = AngieInstantClient()
        self.triggers = BuzzwordTrigger.from_env(cfg.buzzwords)
        self.speech_queue: asyncio.Queue[str] = asyncio.Queue()
        self.stt_audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)

    async def _emit_state(self, state: str, message: str | None = None) -> None:
        if self._on_state:
            await self._on_state(state, message)

    def log_banner(self, mode: str) -> None:
        print(f"[{_ts()}] === {mode} ===")
        print(f"[{_ts()}] Wake words: {', '.join(self.triggers.buzzwords)}")
        if self.cfg.active_voice_agent:
            print(f"[{_ts()}] Active voice agent: {self.cfg.active_voice_agent}")
        print(f"[{_ts()}] Router: {router_mode()}")
        print(f"[{_ts()}] Angie instant ack: {instant_mode()}")
        print(f"[{_ts()}] Agents respond after [final] + {self.scheduler.delay_s:.1f}s silence")
        if partial_trigger_enabled():
            print(
                f"[{_ts()}] Fast path: direct ask in [partial] + "
                f"~{os.getenv('STT_TRIGGER_SILENCE_S', '1.0')}s quiet → router"
            )
        print(f"[{_ts()}] Listening...\n")

    async def deliver_response(self, request: AgentRequest) -> None:
        use_instant = instant_mode() != "off" and should_instant_ack(request)
        spoke_instant = False
        router_task: asyncio.Task | None = None

        if use_instant:
            print(f"[{_ts()}] direct Angie → hold TTS + meeting-router in parallel")
            router_task = asyncio.create_task(
                self.orchestrator.invoke(request, skip_ack=True)
            )
            if instant_mode() == "hold":
                text = hold_ack_text()
                spoke_instant = True
                print(f"[{_ts()}] hold ack → TTS: {text!r}")
                await self._emit_state("speaking", text[:80])
                if self.cfg.speak_response:
                    await self._speak(text, "Angie")
                else:
                    print(f"[{_ts()}] TTS off — hold ack: {text}")
            else:
                instant = await self.angie_instant.generate(request)
                if instant.ok and instant.text.strip():
                    spoke_instant = True
                    print(f"[{_ts()}] instant angie ack → {instant.text!r}")
                    await self._emit_state("speaking", instant.text[:80])
                    if self.cfg.speak_response:
                        await self._speak(instant.text, "Angie")
                    else:
                        print(f"[{_ts()}] TTS off — instant ack: {instant.text}")
                elif instant.error:
                    print(f"[{_ts()}] angie-instant miss — {instant.error}")
            await self._emit_state("thinking", "Consulting meeting-router")
            response = await router_task
            if response.pending_specialist and not spoke_instant:
                fallback = await self.orchestrator.deferred_angie_ack(request)
                if fallback and fallback.text.strip():
                    await self._speak(fallback.text, fallback.agent_name)
        else:
            await self._emit_state("thinking", "Consulting meeting-router")
            response = await self.orchestrator.invoke(request)

        if not response.should_respond and not response.pending_specialist:
            await self._emit_state("listening", "Keeping listening")
            return

        if not self.cfg.speak_response:
            if response.text.strip():
                print(f"[{_ts()}] TTS off — would say: {response.text.strip()}")
            if response.pending_specialist:
                print(f"[{_ts()}] TTS off — would then run {response.pending_specialist}")
            await self._emit_state("listening")
            return

        if response.should_respond and response.text.strip():
            await self._speak(response.text.strip(), response.agent_name)

        if response.pending_specialist:
            await self._emit_state("thinking", f"Running {response.pending_specialist}")
            followup = await self.orchestrator.complete_specialist(
                request, response.pending_specialist
            )
            if followup.should_respond and followup.text.strip():
                followup = await self.orchestrator._speech_editor.prepare(
                    followup, request
                )
                await self._speak(followup.text.strip(), followup.agent_name)

        await self._emit_state("listening")

    async def _speak(self, reply: str, agent_name: str) -> None:
        if not reply.strip():
            return
        self.guard.arm_for_response(reply)
        print(f"[{_ts()}] speaking → {agent_name}: {reply}")
        await self._emit_state("speaking", reply[:80])
        await self.speech_queue.put(reply)
        await wait_playback_done(self.output)
        self.guard.extend(1.0)

    def on_speech_start(self) -> None:
        if self.guard.is_deaf():
            return
        self.scheduler.on_speech_resume()
        self.partial_scheduler.on_speech_resume()
        self.guard.clear()
        self.output.barge_in()
        self.tts.cancel()

    def on_partial(self, text: str, last_text_at: float) -> None:
        if self.guard.is_deaf():
            return
        self.partial_scheduler.on_partial(
            text, last_text_at, self.stt.context, self.triggers, self.deliver_response
        )

    async def on_final(self, utterance: str, context: TranscriptContext) -> None:
        if self.guard.is_deaf():
            return
        self.scheduler.on_new_final()
        mentioned = self.triggers.scan(utterance)
        if not mentioned:
            return

        primary = mentioned[-1] if mentioned else ""
        request = AgentRequest(
            wake_word=primary,
            mentioned_wake_words=mentioned,
            utterance=utterance,
            meeting_transcript=context.as_text(),
            recent_transcript=context.recent(8),
        )
        fast_angie = instant_mode() == "hold" and should_instant_ack(request)
        delay_s = angie_invoke_delay_s() if fast_angie else None
        self.scheduler.schedule(
            mentioned,
            utterance,
            context,
            self.deliver_response,
            delay_s=delay_s,
        )

    async def tts_loop(self) -> None:
        self.output.start()
        while True:
            text = await self.speech_queue.get()
            ok = await self.tts.speak(text, self.output)
            if not ok:
                print(f"[TTS failed] {text}")

    async def run_core(
        self,
        audio_feeder: asyncio.Task,
        *,
        connect: bool = True,
    ) -> None:
        """Run STT/TTS/routing; `audio_feeder` pushes PCM into `stt_audio_queue`."""
        if connect:
            await self.stt.connect()
            await self.tts.connect()

        try:
            await asyncio.gather(
                audio_feeder,
                self.stt.run_sender(self.stt_audio_queue),
                self.stt.run_receiver(
                    on_final=self.on_final,
                    on_speech_start=self.on_speech_start,
                    on_partial=self.on_partial,
                ),
                self.tts_loop(),
            )
        finally:
            audio_feeder.cancel()
            self.scheduler.cancel()
            self.partial_scheduler.cancel()
            self.output.stop()
