"""FastAPI backend for the Meeting Agent (Phase 0).

Responsibilities (PRD section 16):
- Receive a meeting link from the web app.
- Relay a JOIN_MEETING command to the connected worker.
- Track and expose session/worker status for the web app to poll.
- Maintain the worker WebSocket connection.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from meet_urls import normalize_meet_url
from sessions import SessionStore, Status
from ws_worker import WorkerManager

app = FastAPI(title="Meeting Agent Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SessionStore()
worker = WorkerManager(store)


class CreateSessionRequest(BaseModel):
    meeting_url: str
    voice_agent_id: str | None = None


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/worker")
def worker_status() -> dict:
    return worker.info()


@app.post("/sessions")
def create_session(req: CreateSessionRequest) -> dict:
    try:
        url = normalize_meet_url(req.meeting_url)
    except ValueError:
        raise HTTPException(status_code=422, detail="meeting_url is required") from None
    voice_agent_id = req.voice_agent_id
    if voice_agent_id is not None:
        voice_agent_id = voice_agent_id.strip().lower()
        if voice_agent_id not in {"angie"}:
            raise HTTPException(
                status_code=422,
                detail="voice_agent_id must be angie (Nikki and Olaf are subagents)",
            ) from None
    session = store.create(url, voice_agent_id=voice_agent_id)
    return {"session_id": session.id, "status": session.status}


@app.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    data = session.to_dict()
    data["worker_status"] = worker.worker_status
    return data


@app.post("/sessions/{session_id}/start")
async def start_session(session_id: str) -> dict:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    if not worker.online:
        store.update_status(session_id, Status.ERROR.value, "Worker offline")
        raise HTTPException(status_code=409, detail="worker offline")

    sent = await worker.send_command(
        {
            "type": "JOIN_MEETING",
            "session_id": session.id,
            "meeting_url": session.meeting_url,
            "voice_agent_id": session.voice_agent_id,
        }
    )
    if not sent:
        store.update_status(session_id, Status.ERROR.value, "Worker offline")
        raise HTTPException(status_code=409, detail="worker offline")

    store.update_status(session_id, Status.JOINING_MEETING.value, "Sent join command to worker")
    return {"status": Status.JOINING_MEETING.value}


@app.websocket("/worker")
async def worker_ws(socket: WebSocket) -> None:
    worker_id = socket.query_params.get("worker_id", "worker_1")
    await worker.connect(socket, worker_id)
    try:
        while True:
            message = await socket.receive_json()
            worker.handle_message(message)
    except WebSocketDisconnect:
        worker.disconnect(socket)
    except Exception:
        worker.disconnect(socket)
        raise
