#!/usr/bin/env python3
"""Local Meet simulator — mic → agents → speaker (no Google Meet)."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "speech" / "meeting_sim.py"), run_name="__main__")
