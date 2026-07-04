"""In-memory session and worker state for Phase 0.

No database is used in Phase 0 (matches the PRD non-goals). A single worker and
a small set of sessions are tracked in process memory.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock


class Status(str, Enum):
    """Status vocabulary from PRD FR-0.3 / section 17."""

    WORKER_OFFLINE = "worker_offline"
    WORKER_CONNECTED = "worker_connected"
    CREATED = "created"
    JOINING_MEETING = "joining_meeting"
    IN_WAITING_ROOM = "in_waiting_room"
    IN_MEETING = "in_meeting"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class Session:
    id: str
    meeting_url: str
    status: str = Status.CREATED.value
    last_event: str = "Session created"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "session_id": self.id,
            "meeting_url": self.meeting_url,
            "status": self.status,
            "last_event": self.last_event,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SessionStore:
    """Thread-safe, in-memory store for sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def create(self, meeting_url: str) -> Session:
        session = Session(id=f"sess_{uuid.uuid4().hex[:8]}", meeting_url=meeting_url)
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            return self._sessions.get(session_id)

    def update_status(self, session_id: str, status: str, last_event: str | None = None) -> Session | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            session.status = status
            if last_event is not None:
                session.last_event = last_event
            session.updated_at = time.time()
            return session

    def list(self) -> list[Session]:
        with self._lock:
            return list(self._sessions.values())
