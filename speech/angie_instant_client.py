"""Contextual Angie first-line ack — fast local extraction or optional cloud agent."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

from speech.agent_context import AgentRequest
from speech.cursor_cloud_client import invoke_cursor_agent
from speech.router_heuristic import angie_should_delegate_to_nikki, is_direct_agent_call

logger = logging.getLogger(__name__)

SKILL_PATH = "agents/angie-instant/SKILL.md"
_ANGIE_ASK = re.compile(r"angie[,:\s]+(.+)", re.I | re.S)
_OLAF_HINTS = re.compile(
    r"\b(dashboard|screen\s*share|pull\s+up|show\s+(?:me|us)|open\s+(?:the\s+)?url|logs?\s+url)\b",
    re.I,
)


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


DEFAULT_HOLD_ACK_TEXT = "I'm processing your request right now."


def instant_mode() -> str:
    """``hold`` (default) = fixed line after brief delay; ``local`` / ``cloud`` / ``off``."""
    explicit = os.getenv("ANGIE_INSTANT_MODE", "").strip().lower()
    if explicit in {"off", "0", "false", "no"}:
        return "off"
    if explicit in {"hold", "local", "cloud"}:
        return explicit
    if os.getenv("INSTANT_ANGIE_ACK", "1").strip().lower() in {"0", "false", "no"}:
        return "off"
    return "hold"


def hold_ack_text() -> str:
    return os.getenv("ANGIE_HOLD_ACK_TEXT", DEFAULT_HOLD_ACK_TEXT).strip() or DEFAULT_HOLD_ACK_TEXT


def angie_invoke_delay_s() -> float:
    """Silence wait before router when Angie is called directly (0 = invoke on final)."""
    raw = os.getenv("ANGIE_INVOKE_DELAY_S", "0").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0


def should_instant_ack(request: AgentRequest) -> bool:
    """Only fire on a direct call to Angie, not casual mentions."""
    words = request.mentioned_wake_words or [request.wake_word]
    direct, agent = is_direct_agent_call(request.utterance, words)
    return direct and agent == "angie"


@dataclass
class InstantAckResult:
    ok: bool
    text: str = ""
    delegate_to: str | None = None
    error: str | None = None


def _shorten_phrase(text: str, *, max_words: int = 10) -> str:
    text = re.sub(r"\s+", " ", text).strip().rstrip(".,!?")
    if not text:
        return "that"
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _clean_ask(ask: str) -> str:
    t = ask.strip()
    t = re.sub(r"^(?:could|can)\s+you\s+(?:please\s+)?", "", t, flags=re.I)
    t = re.sub(
        r"^(?:please\s+)?(?:find|look(?:\s+at)?|check|take\s+a\s+look(?:\s+at)?|fix|help)\s*",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"^because\s+", "", t, flags=re.I)
    t = re.sub(r"^at the moment\s+", "", t, flags=re.I)
    t = re.sub(r"^we have\s+", "", t, flags=re.I)
    return t.strip() or ask.strip()


def _extract_angie_ask(request: AgentRequest) -> str:
    """Pull the user's actual ask — the words after Angie in the utterance."""
    match = _ANGIE_ASK.search(request.utterance)
    if not match:
        return "that"
    ask = _clean_ask(match.group(1).strip())
    first_sentence = re.split(r"[.!?]", ask, maxsplit=1)[0].strip()
    return _shorten_phrase(first_sentence or ask)


def _delegate_target(request: AgentRequest) -> str | None:
    text = f"{request.utterance} {request.recent_transcript}"
    if _OLAF_HINTS.search(text):
        return "olaf"
    if angie_should_delegate_to_nikki(request):
        return "nikki"
    return None


def _local_instant_ack(request: AgentRequest) -> InstantAckResult:
    ask = _extract_angie_ask(request)
    delegate = _delegate_target(request)
    if delegate == "nikki":
        text = f"Got it — {ask}. I'm handing that to Nikki now."
    elif delegate == "olaf":
        text = f"Got it — {ask}. I'll get Olaf on that."
    else:
        text = f"Got it — {ask}. I'm on it."
    print(f"[{_ts()}] angie-instant (local) → {text!r}")
    return InstantAckResult(ok=True, text=text, delegate_to=delegate)


def _load_skill() -> str:
    root = Path(__file__).resolve().parents[1]
    path = root / SKILL_PATH
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return f"(skill file not found: {SKILL_PATH})"


def _parse_instant_response(raw: str) -> InstantAckResult:
    text = _strip_json_fence(raw)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        cleaned = text.strip()
        if cleaned:
            return InstantAckResult(ok=True, text=cleaned)
        return InstantAckResult(ok=False, error="unparseable instant ack JSON")

    if not isinstance(data, dict):
        return InstantAckResult(ok=False, error="instant ack must be a JSON object")

    spoken = str(data.get("spoken_text", "") or "").strip()
    delegate = data.get("delegate_to")
    if delegate in {"", "none", "null", None}:
        delegate_to = None
    else:
        delegate_to = str(delegate).lower().strip()

    if not spoken:
        return InstantAckResult(ok=False, error="instant ack missing spoken_text")

    return InstantAckResult(ok=True, text=spoken, delegate_to=delegate_to)


def _poll_timeout_s() -> float:
    raw = os.getenv("ANGIE_INSTANT_POLL_TIMEOUT_S", "35").strip()
    try:
        return max(10.0, float(raw))
    except ValueError:
        return 35.0


def _instant_model() -> str | None:
    model = os.getenv("ANGIE_INSTANT_MODEL", "").strip()
    return model or None


def _invoke_cloud(request: AgentRequest) -> InstantAckResult:
    skill = _load_skill()
    prompt = (
        "You are the angie-instant cloud agent. Follow the skill below.\n\n"
        f"--- SKILL ---\n{skill}\n--- END SKILL ---\n\n"
        f"AgentRequest:\n{request.to_json()}\n\n"
        "Return the JSON object (spoken_text, delegate_to) only."
    )
    started = time.monotonic()
    result = invoke_cursor_agent(
        prompt,
        auto_create_pr=False,
        repository="",
        model=_instant_model(),
        poll_timeout_s=_poll_timeout_s(),
    )
    elapsed = time.monotonic() - started
    if not result.ok:
        logger.warning("angie-instant cloud failed in %.1fs: %s", elapsed, result.error)
        return InstantAckResult(ok=False, error=result.error)

    parsed = _parse_instant_response(result.text)
    if parsed.ok:
        logger.info(
            "angie-instant ok in %.1fs delegate=%s text=%r",
            elapsed,
            parsed.delegate_to,
            parsed.text[:80],
        )
        print(f"[{_ts()}] angie-instant ({elapsed:.1f}s) → {parsed.text!r}")
    else:
        logger.warning("angie-instant bad response in %.1fs: %s", elapsed, parsed.error)
    return parsed


class AngieInstantClient:
    """First-line Angie ack while the meeting-router runs in parallel."""

    async def generate(self, request: AgentRequest) -> InstantAckResult:
        mode = instant_mode()
        if mode == "off":
            return InstantAckResult(ok=False, error="angie-instant disabled")
        if not should_instant_ack(request):
            return InstantAckResult(ok=False, error="not a direct Angie call")
        if mode == "hold":
            text = hold_ack_text()
            print(f"[{_ts()}] angie hold ack → {text!r}")
            return InstantAckResult(ok=True, text=text)
        if mode == "local":
            return _local_instant_ack(request)
        return await asyncio.to_thread(_invoke_cloud, request)
