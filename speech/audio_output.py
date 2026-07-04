"""Playback sink protocol — local speaker or Meet virtual mic."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AudioOutput(Protocol):
    """Minimal interface Gradium TTS uses for PCM playback."""

    def start(self) -> None: ...

    def enqueue(self, pcm_bytes: bytes) -> None: ...

    def barge_in(self) -> None: ...

    def busy(self) -> bool: ...

    def stop(self) -> None: ...
