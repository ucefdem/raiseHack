"""Rewrite LLM text into conversational speech before TTS."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass

from speech.agent_context import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

SPEECH_EDITOR_SKILL = "agents/speech-editor/SKILL.md"


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def editor_mode() -> str:
    return os.getenv("SPEECH_EDITOR_MODE", "local").strip().lower()


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


@dataclass
class SpeechScript:
    """Raw LLM output vs spoken script for TTS."""

    raw_text: str
    spoken_text: str
    notes: str | None = None


def parse_editor_response(raw: str, fallback: str) -> SpeechScript:
    """
    Parse JSON from the speech-editor cloud agent.

    See agents/speech-editor/SKILL.md.
    """
    data = json.loads(_strip_json_fence(raw))
    if not isinstance(data, dict):
        raise ValueError("speech editor response must be a JSON object")

    spoken = str(data.get("spoken_text", "") or "").strip()
    notes = str(data.get("notes", "") or "").strip() or None
    raw = str(data.get("raw_text", "") or fallback).strip() or fallback

    if not spoken:
        spoken = _local_prepare(raw, response=response)

    return SpeechScript(raw_text=raw, spoken_text=spoken, notes=notes)


# Phrases that sound robotic in voice — drop or replace
_ROBOTIC_OPENERS = re.compile(
    r"^(?:certainly|of course|absolutely|sure thing|i'd be happy to|i would be happy to|"
    r"great question|thank you for asking)[!,.\s]+",
    re.I,
)

_BULLET = re.compile(r"^\s*[-*•]\s+", re.M)
_NUMBERED = re.compile(r"^\s*\d+\.\s+", re.M)
_FIELD = re.compile(
    r"^(ROOT_CAUSE|FIX_APPLIED|ISSUE_FOUND|ISSUE_FIXED|LOCATION|RECOMMENDED_FIX):\s*(.+)$",
    re.M | re.I,
)


def _yes(value: str | None) -> bool:
    return (value or "").strip().lower() in {"yes", "true", "1"}


def _parse_incident_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in _FIELD.finditer(text):
        fields[match.group(1).lower()] = match.group(2).strip()
    return fields


def _shorten_cause(cause: str) -> str:
    cause = re.sub(r"\s*—\s*", " — ", cause)
    cause = cause.replace(
        "checkout assumed every cart has a total field",
        "checkout crashed on empty carts",
    )
    cause = cause.replace(
        "checkout.py assumes every cart has a total field",
        "checkout crashed on empty carts",
    )
    cause = cause.replace("empty carts raised KeyError", "when the cart had no total")
    cause = cause.replace("empty carts raise KeyError", "when the cart has no total")
    return cause.rstrip(".")


def _shorten_fix_applied(fix: str) -> str:
    fix = fix.replace(
        "replaced cart['total'] with cart.get('total', 0) in checkout.py",
        "defaulting missing cart totals to zero in checkout.py",
    )
    fix = fix.replace(
        "guard already present — cart.get('total', 0)",
        "the guard was already in place",
    )
    fix = re.sub(r"\s*—\s*see checkout_fixed\.py", "", fix, flags=re.I)
    return fix.rstrip(".")


def _incident_to_speech(
    raw: str,
    *,
    agent_name: str,
    routed_to: str | None,
) -> str | None:
    """Turn Nikki's raw incident report into meeting-friendly speech."""
    if "NIKKI INCIDENT REPORT" not in raw and "ROOT_CAUSE:" not in raw:
        return None

    fields = _parse_incident_fields(raw)
    if not fields:
        return None

    cause = _shorten_cause(fields.get("root_cause", ""))
    fix = _shorten_fix_applied(fields.get("fix_applied", fields.get("recommended_fix", "")))
    found = _yes(fields.get("issue_found"))
    fixed = _yes(fields.get("issue_fixed"))
    angie_speaks = "angie" in agent_name.lower() or routed_to == "nikki"

    if not found:
        prefix = "I had Nikki check the code — " if angie_speaks else ""
        return f"{prefix}she couldn't find a matching bug in checkout.py."

    if fixed:
        prefix = "I had Nikki check the code — " if angie_speaks else ""
        return (
            f"{prefix}she found the issue: {cause}. "
            f"She's fixed it in place — {fix}."
        )

    # Found but not fixed (e.g. already patched)
    prefix = "Nikki checked the code — " if angie_speaks else ""
    return (
        f"{prefix}the root cause was {cause}. "
        f"{fix.capitalize() if fix else 'No new change was needed'}."
    )


def _local_prepare(text: str, *, response: AgentResponse | None = None) -> str:
    """
    Lightweight local rewrite — no LLM.

    Strips markdown, tightens phrasing, keeps it short and speakable.
    Cloud agent (SPEECH_EDITOR_MODE=cloud) replaces this in production.
    """
    if response is not None:
        incident_speech = _incident_to_speech(
            text,
            agent_name=response.agent_name,
            routed_to=response.routed_to,
        )
        if incident_speech:
            return incident_speech

    t = text.strip()
    if not t:
        return t

    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"[*_#>`]", "", t)
    t = _BULLET.sub("", t)
    t = _NUMBERED.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = _ROBOTIC_OPENERS.sub("", t).strip()

    # First sentence often enough for a meeting reply
    sentences = re.split(r"(?<=[.!?])\s+", t)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 2:
        t = " ".join(sentences[:2])

    # Soften stiff phrasing
    replacements = [
        (r"\bI will\b", "I'll"),
        (r"\bI am\b", "I'm"),
        (r"\bwe will\b", "we'll"),
        (r"\bcannot\b", "can't"),
        (r"\bdo not\b", "don't"),
    ]
    for pattern, repl in replacements:
        t = re.sub(pattern, repl, t, flags=re.I)

    return t.strip()


class SpeechEditorClient:
    """
    Speech Editor agent — sits between specialist LLM output and Gradium TTS.

    Teammate wires `prepare()` to Cursor Cloud Agent (agents/speech-editor/SKILL.md)
    when SPEECH_EDITOR_MODE=cloud.
    """

    async def prepare(
        self,
        response: AgentResponse,
        request: AgentRequest,
    ) -> AgentResponse:
        if not response.should_respond or not response.text.strip():
            return response

        raw = (response.raw_text or response.text).strip()
        mode = editor_mode()

        if mode == "cloud":
            # TODO (teammate): invoke speech-editor cloud agent with raw + AgentRequest context
            # script = parse_editor_response(cloud_output, raw)
            script = SpeechScript(
                raw_text=raw,
                spoken_text=_local_prepare(raw, response=response),
                notes="SPEECH_EDITOR_MODE=cloud but agent not wired — used local fallback",
            )
        elif mode == "off":
            script = SpeechScript(raw_text=raw, spoken_text=raw)
        else:
            script = SpeechScript(raw_text=raw, spoken_text=_local_prepare(raw, response=response))

        if script.spoken_text != raw:
            print(f"[{_ts()}] speech-editor: raw → spoken")
            print(f"[{_ts()}]   raw:    {raw[:120]}{'...' if len(raw) > 120 else ''}")
            print(f"[{_ts()}]   spoken: {script.spoken_text!r}")
        if script.notes:
            logger.debug("speech-editor notes: %s", script.notes)

        return AgentResponse(
            text=script.spoken_text,
            raw_text=script.raw_text,
            agent_name=response.agent_name,
            routed_to=response.routed_to,
            should_respond=response.should_respond,
            reason=response.reason,
        )
