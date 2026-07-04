"""Orchestrator interface — meeting-router cloud agent plugs in here."""

from __future__ import annotations

import json
import logging
import os
import time

from speech.agent_context import AgentRequest, AgentResponse
from speech.router_heuristic import STUB_REPLIES, is_direct_agent_call
from speech.speech_editor import SpeechEditorClient

logger = logging.getLogger(__name__)

AGENT_MAP = {
    "angie": "Orchestrator (Angie)",
    "nikki": "Sales Agent (Nikki)",
    "olaf": "Computer-Use Agent (Olaf)",
    "meeting-router": "Meeting Router",
}


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def router_mode() -> str:
    return os.getenv("ROUTER_MODE", "heuristic").strip().lower()


def _router_mode() -> str:
    return router_mode()


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def parse_router_response(raw: str, request: AgentRequest) -> AgentResponse:
    """
    Parse JSON from the meeting-router cloud agent.

    See agents/meeting-router/SKILL.md for the contract.
    """
    data = json.loads(_strip_json_fence(raw))
    if not isinstance(data, dict):
        raise ValueError("router response must be a JSON object")

    action = str(data.get("action", "")).lower().strip()
    should_respond = action == "respond" or bool(data.get("should_respond", False))

    routed_to = data.get("routed_to") or data.get("spawn_agent")
    if routed_to in {"", "none", "null", None}:
        routed_to = None
    else:
        routed_to = str(routed_to).lower().strip()

    response_text = str(data.get("response_text", "") or "").strip()
    reason = str(data.get("reason", "") or "").strip() or None

    if not should_respond:
        response_text = ""

    agent_key = routed_to or request.wake_word or "meeting-router"
    agent_name = AGENT_MAP.get(agent_key, f"Agent ({agent_key.title()})")

    return AgentResponse(
        text=response_text,
        agent_name=agent_name,
        routed_to=routed_to,
        should_respond=should_respond,
        reason=reason,
    )


def _heuristic_stub_response(request: AgentRequest) -> AgentResponse:
    """Local dev: approximate meeting-router listen vs respond."""
    words = request.mentioned_wake_words or [request.wake_word]
    direct, routed_to = is_direct_agent_call(request.utterance, words)

    if not direct or not routed_to:
        return AgentResponse(
            text="",
            agent_name=AGENT_MAP["meeting-router"],
            routed_to=None,
            should_respond=False,
            reason="heuristic stub: mention only, keep listening",
        )

    return AgentResponse(
        text=STUB_REPLIES.get(routed_to, "I'm here. Working on that now."),
        agent_name=AGENT_MAP.get(routed_to, f"Agent ({routed_to.title()})"),
        routed_to=routed_to,
        should_respond=True,
        reason=f"heuristic stub: direct call to {routed_to}",
    )


def _passthrough_listen_stub(request: AgentRequest) -> AgentResponse:
    """Always listen — for testing wake-word detection without TTS."""
    return AgentResponse(
        text="",
        agent_name=AGENT_MAP["meeting-router"],
        routed_to=None,
        should_respond=False,
        reason="ROUTER_MODE=listen — always keep listening",
    )


def _stub_response(request: AgentRequest) -> AgentResponse:
    mode = _router_mode()
    if mode == "listen":
        return _passthrough_listen_stub(request)
    return _heuristic_stub_response(request)


class OrchestratorClient:
    """
    Invoke the meeting-router agent with full meeting context.

    Teammate replaces the body of `invoke()` with Cursor Cloud Agent API
    when ROUTER_MODE=cloud.

    All spoken replies pass through SpeechEditorClient before TTS.
    """

    def __init__(self) -> None:
        self._speech_editor = SpeechEditorClient()

    async def invoke(self, request: AgentRequest) -> AgentResponse:
        logger.info("[%s] agent.request %s", _ts(), request.summary_for_log())
        print(f"[{_ts()}] --- AgentRequest → meeting-router ---")
        print(request.to_json())
        print(f"[{_ts()}] ------------------------------------")

        mode = _router_mode()
        if mode == "cloud":
            # TODO (teammate): spawn / resume meeting-router cloud agent, pass request.to_json(),
            # then: response = parse_router_response(cloud_agent_output, request)
            response = AgentResponse(
                text="",
                agent_name=AGENT_MAP["meeting-router"],
                routed_to=None,
                should_respond=False,
                reason="ROUTER_MODE=cloud but cloud agent not wired yet",
            )
        else:
            response = _stub_response(request)

        if response.should_respond and response.text:
            response = await self._speech_editor.prepare(response, request)

        if response.should_respond and response.text:
            logger.info("[%s] agent.response %s", _ts(), response.summary_for_log())
            print(f"[{_ts()}] router → respond: {response.summary_for_log()}")
        else:
            reason = response.reason or "keep listening"
            print(f"[{_ts()}] router → listen: {reason}")

        return response
