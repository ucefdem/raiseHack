"""Worker state machine and status reporting.

States mirror PRD section 17. The reporter pushes STATUS events to the backend
through the WebSocket client so the web app can display live progress.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Awaitable, Callable, Optional

logger = logging.getLogger("worker.status")


class WorkerState(str, Enum):
    IDLE = "idle"
    CONNECTING_TO_BACKEND = "connecting_to_backend"
    READY = "worker_connected"
    JOINING_MEETING = "joining_meeting"
    IN_WAITING_ROOM = "in_waiting_room"
    IN_MEETING = "in_meeting"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


# Emitter signature: (status, message) -> awaitable
Emitter = Callable[[str, Optional[str]], Awaitable[None]]


class StatusReporter:
    """Holds the current session id and forwards status changes to the backend."""

    def __init__(self, emit: Emitter) -> None:
        self._emit = emit
        self.session_id: str | None = None
        self.state: WorkerState = WorkerState.IDLE

    async def set(self, state: WorkerState, message: str | None = None) -> None:
        self.state = state
        logger.info("state=%s message=%s", state.value, message or "")
        await self._emit(state.value, message)
