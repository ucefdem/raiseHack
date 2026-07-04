"""Normalize Google Meet links."""

from __future__ import annotations


def normalize_meet_url(raw: str) -> str:
    url = raw.strip()
    if not url:
        raise ValueError("meeting_url is required")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url.lstrip('/')}"
    return url
