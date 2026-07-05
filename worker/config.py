"""Worker configuration, loaded from environment variables.

Keeping the worker OS-agnostic: audio device names come from config so the same
code runs on Linux (PipeWire null sinks) or macOS (BlackHole). See
docs/AUDIO_SETUP.md for how to create the devices per platform.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Config:
    # Backend connection
    backend_ws_url: str = _get("BACKEND_WS_URL", "ws://localhost:8000/worker")
    worker_id: str = _get("WORKER_ID", "worker_1")
    reconnect_delay_s: float = float(_get("RECONNECT_DELAY_S", "3"))
    heartbeat_interval_s: float = float(_get("HEARTBEAT_INTERVAL_S", "10"))

    # Gradium speech (STT + TTS) — see speech/ and worker/.env.example
    gradium_api_key: str = _get("GRADIUM_API_KEY", "")
    voice_id: str = _get("VOICE_ID", "YTpq7expH9539ERJ")
    language: str = _get("LANGUAGE", "en")
    buzzwords: str = _get("BUZZWORDS", "Angie,Nikki,Olaf")
    stt_sample_rate: int = int(_get("STT_SAMPLE_RATE", "24000"))

    # Audio device names (as reported by the OS / sounddevice).
    # On Linux these are typically the PipeWire monitor/source names; on macOS
    # the BlackHole device name. Empty means "use system default".
    capture_device: str = _get("CAPTURE_DEVICE", "")  # what the worker hears (Meet output)
    playback_device: str = _get("PLAYBACK_DEVICE", "")  # what the worker speaks into (Meet mic)

    # Audio format (capture: Meet output; playback: virtual mic; STT: Gradium)
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
    agent_display_name: str = _get("AGENT_DISPLAY_NAME", "AI Project Agent")
    worker_standby: bool = _get("WORKER_STANDBY", "false").lower() in ("1", "true", "yes")

    @property
    def gradium_configured(self) -> bool:
        key = self.gradium_api_key.strip()
        return key not in {"", "gd_your_key_here", "your_key_here"}

    @property
    def input_chunk_frames(self) -> int:
        return int(self.input_sample_rate * self.chunk_ms / 1000)


config = Config()
