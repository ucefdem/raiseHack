"""Cursor Cloud Agents REST client — text-only tool call used from the voice loop.

Docs: https://cursor.com/docs/cloud-agent/api/endpoints (v1) and /v0 legacy.

We wrap the ``POST /v1/agents`` (create + enqueue initial run) endpoint. The voice
loop treats this as a **tool** invoked when the meeting-router decides the wake
word maps to a cloud agent. Every call is wrapped in ``try/except`` so a network
or auth failure never crashes the Meet session — we return a structured error
that the orchestrator surfaces as a spoken fallback.

Auth: HTTP Basic with ``API_KEY:`` (empty password), per Cursor docs.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


DEFAULT_API_URL = "https://api.cursor.com/v1/agents"
DEFAULT_MODEL = "composer-2"


@dataclass
class CursorAgentResult:
    """Outcome of a Cursor Cloud Agent invocation."""

    ok: bool
    text: str = ""
    agent_id: str | None = None
    run_id: str | None = None
    raw: dict = field(default_factory=dict)
    error: str | None = None


def _cursor_api_url() -> str:
    return os.getenv("CURSOR_AGENTS_API_URL", DEFAULT_API_URL).strip() or DEFAULT_API_URL


def _cursor_model() -> str:
    return os.getenv("CURSOR_AGENTS_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _basic_auth_header(api_key: str) -> str:
    token = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _build_payload(
    prompt_text: str,
    *,
    repository: str | None,
    ref: str | None,
    auto_create_pr: bool,
    mcp_servers: list[dict] | None,
) -> dict:
    payload: dict = {
        "prompt": {"text": prompt_text},
        "model": {"id": _cursor_model()},
    }
    if repository:
        payload["repos"] = [{"url": repository, "startingRef": ref or "main"}]
    if mcp_servers:
        payload["mcpServers"] = mcp_servers
    payload["autoCreatePR"] = bool(auto_create_pr)
    return payload


def _extract_text(response: dict) -> str:
    """Best-effort extraction of the initial run's text output.

    The API returns ``{"agent": {...}, "run": {...}}``. Response shape has
    evolved (v0 vs v1); we handle both defensively.
    """
    run = response.get("run") or response
    for key in ("text", "output", "result", "response", "message"):
        value = run.get(key) if isinstance(run, dict) else None
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def invoke_cursor_agent(
    prompt_text: str,
    *,
    api_key: str | None = None,
    repository: str | None = None,
    ref: str | None = None,
    auto_create_pr: bool = False,
    mcp_servers: list[dict] | None = None,
    timeout_s: float = 30.0,
) -> CursorAgentResult:
    """Send a text prompt to the Cursor Cloud Agents API.

    Never raises: any failure is captured on the returned :class:`CursorAgentResult`.
    Use this as the "tool" the voice loop calls when routing to a cloud agent.
    """
    key = (api_key or os.getenv("CURSOR_API_KEY", "")).strip()
    if not key:
        return CursorAgentResult(ok=False, error="CURSOR_API_KEY is not set")
    if not prompt_text or not prompt_text.strip():
        return CursorAgentResult(ok=False, error="empty prompt")

    url = _cursor_api_url()
    payload = _build_payload(
        prompt_text.strip(),
        repository=repository or os.getenv("CURSOR_AGENTS_REPOSITORY") or None,
        ref=ref or os.getenv("CURSOR_AGENTS_REF") or None,
        auto_create_pr=auto_create_pr,
        mcp_servers=mcp_servers,
    )
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": _basic_auth_header(key),
            "User-Agent": "raisehack-voice-loop/1.0",
        },
    )

    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        logger.warning("cursor agents API %s failed: %s %s", url, exc.code, detail[:500])
        return CursorAgentResult(ok=False, error=f"HTTP {exc.code}: {detail[:200]}")
    except urllib.error.URLError as exc:
        logger.warning("cursor agents API %s network error: %s", url, exc)
        return CursorAgentResult(ok=False, error=f"network error: {exc.reason}")
    except (TimeoutError, OSError) as exc:
        logger.warning("cursor agents API %s IO error: %s", url, exc)
        return CursorAgentResult(ok=False, error=f"io error: {exc}")
    except json.JSONDecodeError as exc:
        logger.warning("cursor agents API returned non-JSON: %s", exc)
        return CursorAgentResult(ok=False, error="invalid JSON response")
    except Exception as exc:  # noqa: BLE001 — never let the voice loop die
        logger.exception("cursor agents API unexpected failure")
        return CursorAgentResult(ok=False, error=f"unexpected: {exc}")

    elapsed = time.monotonic() - started
    if not isinstance(data, dict):
        return CursorAgentResult(ok=False, error="response was not an object", raw={"raw": data})

    agent = data.get("agent") if isinstance(data.get("agent"), dict) else {}
    run = data.get("run") if isinstance(data.get("run"), dict) else {}
    text = _extract_text(data)

    logger.info(
        "cursor agents API ok in %.2fs agent=%s run=%s text_chars=%d",
        elapsed,
        agent.get("id"),
        run.get("id"),
        len(text),
    )
    return CursorAgentResult(
        ok=True,
        text=text,
        agent_id=str(agent.get("id")) if agent.get("id") else None,
        run_id=str(run.get("id")) if run.get("id") else None,
        raw=data,
    )
