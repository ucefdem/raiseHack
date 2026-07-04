"""Worker WebSocket manager.

Phase 0 supports a single dedicated worker. The worker keeps an outbound
WebSocket connection to the backend, receives commands (e.g. JOIN_MEETING) and
streams STATUS events back.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import WebSocket

from sessions import SessionStore, Status


class WorkerManager:
    """Tracks the single connected worker and relays commands/status."""

    def __init__(self, store: SessionStore) -> None:
        self._store = store
        self._socket: WebSocket | None = None
        self._worker_id: str | None = None
        self._last_seen: float = 0.0

    @property
    def online(self) -> bool:
        return self._socket is not None

    @property
    def worker_status(self) -> str:
        return Status.WORKER_CONNECTED.value if self.online else Status.WORKER_OFFLINE.value

    def info(self) -> dict[str, Any]:
        return {
            "worker_id": self._worker_id,
            "online": self.online,
            "worker_status": self.worker_status,
            "last_seen_at": self._last_seen or None,
        }

    async def connect(self, socket: WebSocket, worker_id: str) -> None:
        await socket.accept()
        self._socket = socket
        self._worker_id = worker_id
        self._last_seen = time.time()

    def disconnect(self, socket: WebSocket) -> None:
        if self._socket is socket:
            self._socket = None
            self._worker_id = None

    async def send_command(self, command: dict[str, Any]) -> bool:
        """Send a command to the worker. Returns False if no worker is online."""
        if self._socket is None:
            return False
        await self._socket.send_json(command)
        return True

    def handle_message(self, message: dict[str, Any]) -> None:
        """Process an inbound message from the worker."""
        self._last_seen = time.time()
        msg_type = message.get("type")

        if msg_type == "STATUS":
            session_id = message.get("session_id")
            status = message.get("status")
            event = message.get("message")
            if session_id and status:
                self._store.update_status(session_id, status, event)
        elif msg_type == "HELLO":
            self._worker_id = message.get("worker_id", self._worker_id)
        # HEARTBEAT and unknown types only refresh last_seen.
