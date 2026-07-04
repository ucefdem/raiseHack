"""Shared audio helpers for the speech pipeline."""

from __future__ import annotations

import asyncio

from speech.guard import AgentGuard


async def gated_audio_sender(
    raw_queue: asyncio.Queue[bytes],
    stt_queue: asyncio.Queue[bytes],
    guard: AgentGuard,
) -> None:
    """Drop frames while agent TTS plays (local sim path)."""
    while True:
        pcm = await raw_queue.get()
        if not guard.is_deaf():
            try:
                stt_queue.put_nowait(pcm)
            except asyncio.QueueFull:
                pass
