"""Worker configuration, loaded from environment variables.

Keeping the worker OS-agnostic: audio device names come from config so the same
code runs on Linux (PipeWire null sinks) or macOS (BlackHole). See
docs/AUDIO_SETUP.md for how to create the devices per platform.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Config:
    # Backend connection
    backend_ws_url: str = _get("BACKEND_WS_URL", "ws://localhost:8000/worker")
    worker_id: str = _get("WORKER_ID", "worker_1")
    reconnect_delay_s: float = float(_get("RECONNECT_DELAY_S", "3"))
    heartbeat_interval_s: float = float(_get("HEARTBEAT_INTERVAL_S", "10"))

    # Gemini Live
    # NOTE: model IDs differ between the Gemini Developer API (AI Studio key) and
    # Vertex AI. These defaults are Developer-API names. Run `list_models.py` to
    # see which Live models your key supports (must support bidiGenerateContent).
    gemini_api_key: str = _get("GEMINI_API_KEY", "")
    gemini_model: str = _get("GEMINI_MODEL", "gemini-2.5-flash-native-audio-latest")
    gemini_voice: str = _get("GEMINI_VOICE", "Puck")
    # Empty = use SDK default (v1beta). Set to "v1alpha" to enable proactive audio.
    gemini_api_version: str = _get("GEMINI_API_VERSION", "")
    # Proactive audio (model decides when to reply) is a v1alpha native-audio
    # feature; sending it on v1beta fails setup ("Unknown name proactivity").
    gemini_proactive_audio: bool = _get("GEMINI_PROACTIVE_AUDIO", "false").lower() in ("1", "true", "yes")

    # Agent identity / behaviour
    agent_display_name: str = _get("AGENT_DISPLAY_NAME", "AI Project Agent")

    # Audio device names (as reported by the OS / sounddevice).
    # On Linux these are typically the PipeWire monitor/source names; on macOS
    # the BlackHole device name. Empty means "use system default".
    capture_device: str = _get("CAPTURE_DEVICE", "")  # what the worker hears (Meet output)
    playback_device: str = _get("PLAYBACK_DEVICE", "")  # what the worker speaks into (Meet mic)

    # Audio format (Gemini Live: 16k in, 24k out, mono, 16-bit PCM)
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
    channels: int = 1
    chunk_ms: int = 20

    # Chrome / Playwright
    chrome_user_data_dir: str = _get(
        "CHROME_USER_DATA_DIR",
        os.path.expanduser("~/.meeting-agent/chrome-profile"),
    )
    chrome_channel: str = _get("CHROME_CHANNEL", "chrome")  # use installed Chrome, not bundled Chromium
    headless: bool = _get("HEADLESS", "false").lower() in ("1", "true", "yes")

    @property
    def input_chunk_frames(self) -> int:
        return int(self.input_sample_rate * self.chunk_ms / 1000)


config = Config()
