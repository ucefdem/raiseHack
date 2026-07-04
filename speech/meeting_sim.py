#!/usr/bin/env python3
"""
Simulated Google Meet — mic in, speaker out.

Pipeline:
  mic → real-time STT (constant context) → wake word? → meeting-router → TTS (if respond)

Run:
  export GRADIUM_API_KEY=...
  python -m speech.meeting_sim
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import time

from speech.agent_context import AgentRequest
from speech.audio_io import AudioPlayer, MicCapture
from speech.guard import AgentGuard
from speech.invoke_scheduler import AgentInvokeScheduler
from speech.orchestrator import OrchestratorClient, router_mode
from speech.partial_scheduler import PartialTriggerScheduler, partial_trigger_enabled
from speech.stt import GradiumSTT, TranscriptContext
from speech.triggers import BuzzwordTrigger
from speech.tts import GradiumTTS

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DEFAULT_VOICE_ID = "YTpq7expH9539ERJ"


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def validate_env() -> dict:
    gradium_key = os.getenv("GRADIUM_API_KEY", "").strip()
    voice_id = os.getenv("VOICE_ID", DEFAULT_VOICE_ID).strip()
    language = os.getenv("LANGUAGE", "en").strip()
    buzzwords = os.getenv("BUZZWORDS", "").strip() or None
    speak_response = os.getenv("SPEAK_RESPONSE", "1").strip() != "0"

    if not gradium_key:
        print(
            "Missing GRADIUM_API_KEY.\n"
            "  export GRADIUM_API_KEY=gd_your_key\n"
            "  export VOICE_ID=YTpq7expH9539ERJ  # optional\n"
            "  export BUZZWORDS=Angie,Nikki,Olaf  # optional wake words\n"
            "  export SPEAK_RESPONSE=1            # TTS the agent reply (default on)",
            file=sys.stderr,
        )
        sys.exit(1)

    return {
        "gradium_key": gradium_key,
        "voice_id": voice_id,
        "language": language,
        "buzzwords": buzzwords,
        "speak_response": speak_response,
    }


async def gated_audio_sender(
    raw_queue: asyncio.Queue[bytes],
    stt_queue: asyncio.Queue[bytes],
    guard: AgentGuard,
) -> None:
    """Drop mic frames while agent TTS plays — prevents STT hearing the speaker."""
    while True:
        pcm = await raw_queue.get()
        if not guard.is_deaf():
            try:
                stt_queue.put_nowait(pcm)
            except asyncio.QueueFull:
                pass


async def wait_playback_done(player: AudioPlayer, timeout_s: float = 30.0) -> None:
    """Wait until TTS enqueues audio, then until the speaker buffer drains."""
    deadline = time.monotonic() + timeout_s
    while not player.busy() and time.monotonic() < deadline:
        await asyncio.sleep(0.05)
    while player.busy() and time.monotonic() < deadline:
        await asyncio.sleep(0.1)
    await asyncio.sleep(0.4)


async def main() -> None:
    cfg = validate_env()

    raw_audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)
    stt_audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)
    speech_queue: asyncio.Queue[str] = asyncio.Queue()

    player = AudioPlayer()
    guard = AgentGuard()
    scheduler = AgentInvokeScheduler.from_env()
    partial_scheduler = PartialTriggerScheduler.from_env()
    mic = MicCapture(raw_audio_queue)
    stt = GradiumSTT(api_key=cfg["gradium_key"], language=cfg["language"])
    tts = GradiumTTS(api_key=cfg["gradium_key"], voice_id=cfg["voice_id"])
    orchestrator = OrchestratorClient()
    triggers = BuzzwordTrigger.from_env(cfg["buzzwords"])

    print(f"[{_ts()}] === Meet Simulator ===")
    print(f"[{_ts()}] Wake words: {', '.join(triggers.buzzwords)} (any mention → meeting-router)")
    print(f"[{_ts()}] Router: {router_mode()} stub (cloud agent → agents/meeting-router/SKILL.md)")
    print(f"[{_ts()}] Agents respond after [final] + {scheduler.delay_s:.1f}s silence")
    if partial_trigger_enabled():
        print(
            f"[{_ts()}] Fast path: direct ask in [partial] + "
            f"~{os.getenv('STT_TRIGGER_SILENCE_S', '1.0')}s quiet → router"
        )
    print(f"[{_ts()}] Context [final]s need ~{os.getenv('STT_FINAL_SILENCE_S', '5')}s pause in speech")
    print(f"[{_ts()}] Try: \"What about Angie, pull up the dashboard?\" then stop.\n")

    async def deliver_response(request: AgentRequest) -> None:
        if guard.is_deaf():
            print(f"[{_ts()}] skipped invoke — agent still speaking")
            return
        response = await orchestrator.invoke(request)
        if not response.should_respond or not response.text.strip():
            return
        if not cfg["speak_response"]:
            print(f"[{_ts()}] TTS off (SPEAK_RESPONSE=0) — would say: {response.text.strip()}")
            return
        reply = response.text.strip()
        guard.arm_for_response(reply)
        print(f"[{_ts()}] speaking → {response.agent_name}: {reply}")
        await speech_queue.put(reply)
        await wait_playback_done(player)
        guard.extend(1.0)

    def on_speech_start() -> None:
        scheduler.on_speech_resume()
        partial_scheduler.on_speech_resume()
        if guard.is_deaf():
            return
        guard.clear()
        player.barge_in()
        tts.cancel()

    def on_partial(text: str, last_text_at: float) -> None:
        if guard.is_deaf():
            return
        partial_scheduler.on_partial(
            text, last_text_at, stt.context, triggers, deliver_response
        )

    async def on_final(utterance: str, context: TranscriptContext) -> None:
        if guard.is_deaf():
            return

        # Any new final resets the wait — user may still be mid-thought
        scheduler.on_new_final()

        mentioned = triggers.scan(utterance)
        if not mentioned:
            return

        scheduler.schedule(mentioned, utterance, context, deliver_response)

    async def tts_loop() -> None:
        player.start()
        while True:
            text = await speech_queue.get()
            ok = await tts.speak(text, player)
            if not ok:
                print(f"[TTS failed] {text}")

    await stt.connect()
    await tts.connect()

    print(f"[{_ts()}] Audio: mic 24kHz in, speaker 48kHz out")
    print(f"[{_ts()}] Listening...\n")

    loop = asyncio.get_running_loop()

    def _shutdown() -> None:
        scheduler.cancel()
        partial_scheduler.cancel()
        for task in asyncio.all_tasks(loop):
            if task is not asyncio.current_task():
                task.cancel()
        player.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    await asyncio.gather(
        mic.run(),
        gated_audio_sender(raw_audio_queue, stt_audio_queue, guard),
        stt.run_sender(stt_audio_queue),
        stt.run_receiver(
            on_final=on_final,
            on_speech_start=on_speech_start,
            on_partial=on_partial,
        ),
        tts_loop(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMeet ended.")
