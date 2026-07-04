"""Outbound WebSocket client to the hosted backend.

Maintains the connection, auto-reconnects, sends heartbeats and status events,
and dispatches inbound commands (e.g. JOIN_MEETING) to a handler.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

import websockets

from config import config

logger = logging.getLogger("worker.ws")

CommandHandler = Callable[[dict[str, Any]], Awaitable[None]]


class BackendClient:
    def __init__(self, on_command: CommandHandler) -> None:
        self._on_command = on_command
        self._ws: Any = None
        self._connected = asyncio.Event()

    async def _send(self, payload: dict[str, Any]) -> None:
        ws = self._ws
        if ws is None:
            return
        try:
            await ws.send(json.dumps(payload))
        except Exception as exc:  # noqa: BLE001
            logger.warning("send failed: %s", exc)

    async def send_status(self, status: str, message: str | None, session_id: str | None) -> None:
        await self._send(
            {
                "type": "STATUS",
                "session_id": session_id,
                "status": status,
                "message": message,
            }
        )

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(config.heartbeat_interval_s)
            await self._send({"type": "HEARTBEAT", "worker_id": config.worker_id})

    async def _handle_connection(self, ws: Any) -> None:
        self._ws = ws
        self._connected.set()
        await self._send({"type": "HELLO", "worker_id": config.worker_id})
        logger.info("connected to backend at %s", config.backend_ws_url)

        heartbeat = asyncio.create_task(self._heartbeat_loop())
        try:
            async for raw in ws:
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("ignoring non-JSON message: %r", raw)
                    continue
                logger.info("received command: %s", message.get("type"))
                asyncio.create_task(self._on_command(message))
        finally:
            heartbeat.cancel()
            self._ws = None
            self._connected.clear()

    async def run_forever(self) -> None:
        """Connect and reconnect until cancelled."""
        while True:
            try:
                async with websockets.connect(
                    f"{config.backend_ws_url}?worker_id={config.worker_id}"
                ) as ws:
                    await self._handle_connection(ws)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("connection error: %s", exc)
            logger.info("reconnecting in %.1fs", config.reconnect_delay_s)
            await asyncio.sleep(config.reconnect_delay_s)
