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
        spoken = _local_prepare(raw)

    return SpeechScript(raw_text=raw, spoken_text=spoken, notes=notes)


# Phrases that sound robotic in voice — drop or replace
_ROBOTIC_OPENERS = re.compile(
    r"^(?:certainly|of course|absolutely|sure thing|i'd be happy to|i would be happy to|"
    r"great question|thank you for asking)[!,.\s]+",
    re.I,
)

_BULLET = re.compile(r"^\s*[-*•]\s+", re.M)
_NUMBERED = re.compile(r"^\s*\d+\.\s+", re.M)


def _local_prepare(text: str) -> str:
    """
    Lightweight local rewrite — no LLM.

    Strips markdown, tightens phrasing, keeps it short and speakable.
    Cloud agent (SPEECH_EDITOR_MODE=cloud) replaces this in production.
    """
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

        raw = response.text.strip()
        mode = editor_mode()

        if mode == "cloud":
            # TODO (teammate): invoke speech-editor cloud agent with raw + AgentRequest context
            # script = parse_editor_response(cloud_output, raw)
            script = SpeechScript(
                raw_text=raw,
                spoken_text=_local_prepare(raw),
                notes="SPEECH_EDITOR_MODE=cloud but agent not wired — used local fallback",
            )
        elif mode == "off":
            script = SpeechScript(raw_text=raw, spoken_text=raw)
        else:
            script = SpeechScript(raw_text=raw, spoken_text=_local_prepare(raw))

        if script.spoken_text != raw:
            print(f"[{_ts()}] speech-editor: {raw[:60]!r} → {script.spoken_text!r}")
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
