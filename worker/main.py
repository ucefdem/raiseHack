"""Worker entrypoint: connects to the backend and runs the join/hear/speak loop.

Sequence on JOIN_MEETING:
  1. Launch Chrome (persistent agent profile) and join the Meet.
  2. Start the audio router (capture Meet output, play into Meet mic).
  3. Open a Gemini Live session and bridge audio both ways.
Status is reported to the backend at each step.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from audio_router import AudioRouter
from config import config
from gemini_live_client import GeminiLiveClient
from meet_controller import MeetController
from status import StatusReporter, WorkerState
from websocket_client import BackendClient

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
                await self._run_session(message["meeting_url"])
            except Exception as exc:  # noqa: BLE001
                logger.exception("session failed")
                await self._reporter.set(WorkerState.ERROR, f"Session failed: {exc}")
            finally:
                self._busy = False

    async def _run_session(self, meeting_url: str) -> None:
        await self._reporter.set(WorkerState.JOINING_MEETING, "Opening Chrome and joining Meet")
        await self._meet.start()
        await self._meet.join(meeting_url)

        if not await self._meet.wait_until_in_meeting():
            await self._reporter.set(WorkerState.ERROR, "Timed out waiting to enter meeting")
            return
        await self._reporter.set(WorkerState.IN_MEETING, "Agent joined the meeting")

        self._audio.start()
        await self._reporter.set(WorkerState.LISTENING, "Listening to the meeting")

        gemini = GeminiLiveClient(
            on_audio=self._audio.play,
            on_state=self._on_gemini_state,
            on_interrupt=self._audio.clear_playback,
        )
        try:
            await gemini.run(self._audio.capture_chunks())
        finally:
            self._audio.stop()

    async def _on_gemini_state(self, state: str) -> None:
        mapping = {
            "listening": WorkerState.LISTENING,
            "speaking": WorkerState.SPEAKING,
            "thinking": WorkerState.THINKING,
        }
        target = mapping.get(state)
        if target and target != self._reporter.state:
            await self._reporter.set(target)

    async def run(self) -> None:
        logger.info("worker starting; backend=%s", config.backend_ws_url)
        await self._backend.run_forever()


def main() -> None:
    try:
        asyncio.run(Worker().run())
    except KeyboardInterrupt:
        logger.info("worker stopped")


if __name__ == "__main__":
    main()
