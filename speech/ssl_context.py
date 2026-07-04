"""SSL context for WebSocket connections (fixes macOS cert issues)."""

from __future__ import annotations

import ssl

import certifi


def websocket_ssl_context() -> ssl.SSLContext:
    """CA bundle that works when system Python certs are missing (common on macOS)."""
    return ssl.create_default_context(cafile=certifi.where())
