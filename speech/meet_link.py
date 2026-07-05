"""Shared Google Meet link — one link for every agent in the office.

All agents (Olaf, Nikki, Angie, Speech loop, apps/api meet stub) resolve the
target Meet URL through this module so the room is consistent end-to-end.

Precedence (first non-empty wins):
  1. Explicit override argument.
  2. ``SHARED_MEET_URL`` env var (canonical name used across services).
  3. ``GOOGLE_MEET_URL`` env var (legacy, keeps existing SKILL.md examples working).
  4. Empty string — caller must handle "no link configured".
"""

from __future__ import annotations

import os


SHARED_MEET_URL_ENV = "SHARED_MEET_URL"
LEGACY_MEET_URL_ENV = "GOOGLE_MEET_URL"


def shared_meet_url(override: str | None = None) -> str:
    """Return the shared Meet URL for every agent in the office.

    Never raises; missing config returns ``""`` so callers can log/degrade.
    """
    for candidate in (override, os.getenv(SHARED_MEET_URL_ENV), os.getenv(LEGACY_MEET_URL_ENV)):
        if candidate and candidate.strip():
            return candidate.strip()
    return ""


def require_shared_meet_url(override: str | None = None) -> str:
    """Same as :func:`shared_meet_url` but raises when nothing is configured."""
    url = shared_meet_url(override)
    if not url:
        raise RuntimeError(
            f"No shared Meet link configured. Set {SHARED_MEET_URL_ENV} in your env."
        )
    return url
