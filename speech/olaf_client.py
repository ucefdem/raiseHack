"""Olaf computer-use agent — Cursor Cloud Agent spawn interface."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass

from speech.agent_context import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

OLAF_SKILL = "agents/olaf/SKILL.md"


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def olaf_mode() -> str:
    return os.getenv("OLAF_MODE", "stub").strip().lower()


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


@dataclass
class OlafResult:
    status: str
    action: str
    response_text: str
    artifacts: list[str]
    notes: str | None = None


def parse_olaf_response(raw: str, fallback_text: str = "") -> OlafResult:
    """Parse JSON from Olaf cloud agent. See agents/olaf/SKILL.md."""
    data = json.loads(_strip_json_fence(raw))
    if not isinstance(data, dict):
        raise ValueError("Olaf response must be a JSON object")

    return OlafResult(
        status=str(data.get("status", "completed")),
        action=str(data.get("action", "unknown")),
        response_text=str(data.get("response_text", "") or fallback_text).strip(),
        artifacts=list(data.get("artifacts") or []),
        notes=str(data.get("notes", "") or "").strip() or None,
    )


def _build_olaf_prompt(request: AgentRequest) -> str:
    meet_url = os.getenv("GOOGLE_MEET_URL", "").strip()
    return (
        f"Read and follow {OLAF_SKILL}.\n\n"
        f"AgentRequest:\n{request.to_json()}\n\n"
        f"Default Meet URL (if needed): {meet_url or '(not set — parse from utterance)'}\n\n"
        "Perform the computer-use task on your cloud VM browser/desktop.\n"
        "Return JSON only (status, action, response_text, artifacts, notes)."
    )


class OlafClient:
    """
    Spawn Olaf on a Cursor Cloud Agent VM with computer use.

    Set OLAF_MODE=cloud and CURSOR_API_KEY to run for real.
    """

    async def execute(self, request: AgentRequest) -> AgentResponse:
        mode = olaf_mode()

        if mode == "cloud":
            return await self._execute_cloud(request)
        return self._execute_stub(request)

    async def _execute_cloud(self, request: AgentRequest) -> AgentResponse:
        api_key = os.getenv("CURSOR_API_KEY", "").strip()
        if not api_key:
            return self._failed(request, "OLAF_MODE=cloud but CURSOR_API_KEY not set")

        # TODO: wire cursor-sdk when ready on feature/agents branch
        # from cursor_sdk import Agent, AgentOptions, CloudAgentOptions
        # result = Agent.prompt(_build_olaf_prompt(request), AgentOptions(...))
        # parsed = parse_olaf_response(result.result, "")
        print(f"[{_ts()}] olaf: cloud spawn not wired yet — install cursor-sdk and uncomment")
        return self._execute_stub(request)

    def _execute_stub(self, request: AgentRequest) -> AgentResponse:
        utterance = request.utterance.lower()
        if "mute" in utterance:
            action, text = "mute_self", "Got it — I'm muted in the Meet."
        elif "share" in utterance or "screen" in utterance or "dashboard" in utterance:
            action, text = "share_screen", "I'll join the Meet and share that screen now."
        elif "open" in utterance or "show" in utterance or "pull up" in utterance:
            action, text = "open_url", "Opening that in the browser now."
        else:
            action, text = "join_meet", "I'm on it — joining the Meet now."

        print(f"[{_ts()}] olaf (stub): action={action}")
        return AgentResponse(
            text=text,
            agent_name="Computer-Use Agent (Olaf)",
            routed_to="olaf",
            should_respond=True,
            reason=f"olaf stub: {action}",
        )

    def _failed(self, request: AgentRequest, reason: str) -> AgentResponse:
        return AgentResponse(
            text="",
            agent_name="Computer-Use Agent (Olaf)",
            routed_to="olaf",
            should_respond=False,
            reason=reason,
        )
