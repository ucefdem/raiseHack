"""Standalone audio verification (PRD milestones M3 and M4).

Validates the two halves of the audio loop independently, before wiring Gemini:

  python verify_audio.py devices     # list all audio devices + indices
  python verify_audio.py speak       # play a test tone into the Meet mic (M4)
  python verify_audio.py listen      # show a live level meter of Meet output (M3)

Set CAPTURE_DEVICE / PLAYBACK_DEVICE env vars to target the virtual devices.
"""

from __future__ import annotations

import math
import sys
import time

import numpy as np
import sounddevice as sd

from audio_router import find_device
from config import config


def list_devices() -> None:
    print(sd.query_devices())


def speak() -> None:
    """Play a 2s 440 Hz tone into the playback (virtual mic) device."""
    device = find_device(config.playback_device, "output")
    rate = config.output_sample_rate
    seconds = 2.0
    t = np.linspace(0, seconds, int(rate * seconds), endpoint=False)
    tone = (0.3 * np.sin(2 * math.pi * 440 * t)).astype(np.float32)
    print(f"Playing 440 Hz test tone into device={device or 'default'} @ {rate} Hz ...")
    sd.play(tone, samplerate=rate, device=device)
    sd.wait()
    print("Done. Meeting participants should have heard the tone.")


def listen() -> None:
    """Print an RMS level meter of the capture (Meet output) device."""
    device = find_device(config.capture_device, "input")
    rate = config.input_sample_rate
    print(f"Listening on device={device or 'default'} @ {rate} Hz. Ctrl-C to stop.")

    def callback(indata, frames, time_info, status) -> None:  # noqa: ANN001
        rms = float(np.sqrt(np.mean(np.square(indata))))
        bars = int(min(rms * 5000, 50))
        print("\r[" + "#" * bars + " " * (50 - bars) + f"] rms={rms:.4f}", end="")

    with sd.InputStream(samplerate=rate, channels=1, dtype="float32", device=device, callback=callback):
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopped.")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "devices"
    if cmd == "devices":
        list_devices()
    elif cmd == "speak":
        speak()
    elif cmd == "listen":
        listen()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
