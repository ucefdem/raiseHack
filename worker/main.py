"""Worker entrypoint: joins Google Meet and runs the Gradium speech agent pipeline.

Sequence on JOIN_MEETING:
  1. Launch Chrome and join the Meet.
  2. Start virtual audio routing (capture Meet output, play into Meet mic).
  3. Stream captured audio → Gradium STT → meeting-router → TTS → virtual mic.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# Repo root on path so worker can import speech.*
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audio_router import AudioRouter
from config import config
from meet_controller import MeetController
from speech_bridge import MeetAudioOutput, meet_capture_to_stt
from status import StatusReporter, WorkerState
from websocket_client import BackendClient

from speech.meeting_session import (
    MeetingSpeechSession,
    speech_config_from_env,
    verify_gradium,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("worker.main")


class Worker:
    def __init__(self) -> None:
        self._backend = BackendClient(self._on_command)
        self._reporter = StatusReporter(self._emit_status)
        self._meet = MeetController()
        self._audio = AudioRouter()
        self._busy = False

    async def _emit_status(self, status: str, message: str | None) -> None:
        await self._backend.send_status(status, message, self._reporter.session_id)

    async def _on_command(self, message: dict[str, Any]) -> None:
        if message.get("type") == "JOIN_MEETING":
            if self._busy:
                logger.warning("already in a session; ignoring JOIN_MEETING")
                return
            self._busy = True
            self._reporter.session_id = message.get("session_id")
            try:
                await self._run_session(
                    message["meeting_url"],
                    voice_agent_id=message.get("voice_agent_id"),
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("session failed")
                await self._reporter.set(WorkerState.ERROR, f"Session failed: {exc}")
            finally:
                self._busy = False

    async def _on_speech_state(self, state: str, message: str | None) -> None:
        mapping = {
            "listening": WorkerState.LISTENING,
            "thinking": WorkerState.THINKING,
            "speaking": WorkerState.SPEAKING,
        }
        target = mapping.get(state)
        if target:
            await self._reporter.set(target, message)

    async def _run_standby_session(
        self, meeting_url: str, voice_agent_id: str | None = None
    ) -> None:
        agent = (voice_agent_id or "angie").strip().lower()
        await self._reporter.set(
            WorkerState.JOINING_MEETING,
            f"Standby: simulating deploy for {agent}",
        )
        await asyncio.sleep(1.2)
        await self._reporter.set(
            WorkerState.IN_MEETING,
            f"Standby: would join {meeting_url}",
        )
        await asyncio.sleep(0.8)
        await self._reporter.set(
            WorkerState.LISTENING,
            "Standby mode — set GRADIUM_API_KEY in worker/.env for live Meet + voice",
        )

    async def _run_session(
        self, meeting_url: str, voice_agent_id: str | None = None
    ) -> None:
        if config.worker_standby or not config.gradium_configured:
            await self._run_standby_session(meeting_url, voice_agent_id)
            return

        active = (voice_agent_id or "").strip().lower() or None
        buzzwords = None
        if active and active != "angie":
            buzzwords = active.capitalize()
            logger.info("session locked to voice agent: %s", active)
        elif active == "angie":
            logger.info("session managed by Angie (delegates to Nikki/Olaf)")

        cfg = speech_config_from_env(
            buzzwords=buzzwords,
            active_voice_agent=active,
        )

        output = MeetAudioOutput(self._audio)
        session = MeetingSpeechSession(cfg, output, on_state=self._on_speech_state)

        # Connect Gradium before Chrome — don't join Meet with a bad API key
        await self._reporter.set(WorkerState.JOINING_MEETING, "Connecting to Gradium STT/TTS")
        try:
            await session.stt.connect()
            await session.tts.connect()
        except RuntimeError as exc:
            msg = str(exc)
            if "Invalid or expired API key" in msg or "STT setup failed" in msg:
                raise RuntimeError(
                    "Gradium API key rejected. Update GRADIUM_API_KEY in worker/.env. "
                ) from exc
            raise

        await self._reporter.set(WorkerState.JOINING_MEETING, "Opening Chrome and joining Meet")
        await self._meet.start()
        await self._meet.join(meeting_url)

        if not await self._meet.wait_until_in_meeting():
            await self._reporter.set(WorkerState.ERROR, "Timed out waiting to enter meeting")
            return
        await self._reporter.set(WorkerState.IN_MEETING, "Agent joined the meeting")

        self._audio.start()
        await self._reporter.set(WorkerState.LISTENING, "Listening to the meeting")
        session.log_banner("Google Meet Agent")

        feeder = asyncio.create_task(
            meet_capture_to_stt(self._audio, session.stt_audio_queue, session.guard)
        )
        try:
            await session.run_core(feeder, connect=False)
        finally:
            self._audio.stop()
            await self._meet.stop()

    async def run(self) -> None:
        logger.info("worker starting; backend=%s", config.backend_ws_url)
        await self._backend.run_forever()


def main() -> None:
    standby = config.worker_standby or not config.gradium_configured
    if standby:
        logger.warning(
            "Worker standby mode — backend connection only; Meet join is simulated. "
            "Set GRADIUM_API_KEY in worker/.env for live audio."
        )
    else:
        try:
            cfg = speech_config_from_env()
            asyncio.run(verify_gradium(cfg))
            logger.info("Gradium API key OK")
        except RuntimeError as exc:
            logger.error("%s", exc)
            sys.exit(1)

    try:
        asyncio.run(Worker().run())
    except KeyboardInterrupt:
        logger.info("worker stopped")


if __name__ == "__main__":
    main()
