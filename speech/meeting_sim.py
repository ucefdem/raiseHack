#!/usr/bin/env python3
"""
Simulated Google Meet — mic in, speaker out.

Same agent pipeline as the worker (meeting-router → Angie → Nikki → speech-editor → TTS),
without Chrome or Google Meet.

Run from worker/ (loads worker/.env automatically):

    cd worker && uv run python run_meeting_sim.py

Or from repo root:

    cd worker && uv run python ../speech/meeting_sim.py

Say clearly: "Angie, a customer says checkout crashes when the cart is empty."
Wait ~2s silence after you finish speaking so the invoke scheduler fires.

Env (from worker/.env):
  GRADIUM_API_KEY   — required (STT + TTS)
  CURSOR_API_KEY    — required if ROUTER_MODE=cloud
  ROUTER_MODE       — heuristic | cloud | listen
  SPEAK_RESPONSE=0  — log agent text only, no TTS audio
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path


def _load_worker_env() -> None:
    """Load worker/.env so sim uses the same keys as the Meet worker."""
    env_path = Path(__file__).resolve().parents[1] / "worker" / ".env"
    if not env_path.is_file():
        env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()


_load_worker_env()

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
