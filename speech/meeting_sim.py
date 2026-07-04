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
import signal
import sys

from speech.audio_io import AudioPlayer, MicCapture
from speech.meet_audio import gated_audio_sender
from speech.meeting_session import MeetingSpeechSession, speech_config_from_env

logging.basicConfig(level=logging.INFO, format="%(message)s")


async def main() -> None:
    try:
        cfg = speech_config_from_env()
    except RuntimeError as exc:
        print(f"{exc}", file=sys.stderr)
        sys.exit(1)

    raw_audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)
    player = AudioPlayer()
    session = MeetingSpeechSession(cfg, player)
    mic = MicCapture(raw_audio_queue)

    session.log_banner("Meet Simulator")

    loop = asyncio.get_running_loop()

    def _shutdown() -> None:
        for task in asyncio.all_tasks(loop):
            if task is not asyncio.current_task():
                task.cancel()
        player.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    feeder = asyncio.create_task(
        gated_audio_sender(raw_audio_queue, session.stt_audio_queue, session.guard)
    )
    await asyncio.gather(
        mic.run(),
        session.run_core(feeder),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMeet ended.")
