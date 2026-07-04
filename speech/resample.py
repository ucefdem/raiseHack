"""Lightweight PCM16 resampling for bridging Meet audio rates to Gradium."""

from __future__ import annotations

import numpy as np


def resample_pcm16(pcm: bytes, from_rate: int, to_rate: int) -> bytes:
    """Resample mono int16 PCM between sample rates."""
    if from_rate == to_rate or not pcm:
        return pcm
    samples = np.frombuffer(pcm, dtype=np.int16)
    if len(samples) == 0:
        return pcm
    n_out = max(int(len(samples) * to_rate / from_rate), 1)
    x_old = np.arange(len(samples), dtype=np.float64)
    x_new = np.linspace(0, len(samples) - 1, n_out)
    out = np.interp(x_new, x_old, samples.astype(np.float64)).astype(np.int16)
    return out.tobytes()
