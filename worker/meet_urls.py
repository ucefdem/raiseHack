"""Normalize Google Meet links for Playwright navigation."""

from __future__ import annotations


def normalize_meet_url(raw: str) -> str:
    """
    Accept full URLs or bare host/path (e.g. meet.google.com/abc-defg-hij).

    Playwright requires a scheme; users often paste without https://.
    """
    url = raw.strip()
    if not url:
        raise ValueError("meeting_url is required")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url.lstrip('/')}"
    return url
