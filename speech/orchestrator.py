"""Orchestrator interface — meeting-router cloud agent plugs in here."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from speech.agent_context import AgentRequest, AgentResponse
from speech.cursor_cloud_client import invoke_cursor_agent
from speech.meet_link import shared_meet_url
from speech.nikki_client import NikkiClient
from speech.olaf_client import OlafClient
from speech.router_heuristic import STUB_REPLIES, angie_should_delegate_to_nikki, is_direct_agent_call
from speech.speech_editor import SpeechEditorClient

logger = logging.getLogger(__name__)

AGENT_MAP = {
    "angie": "Orchestrator (Angie)",
    "nikki": "Code Agent (Nikki)",
    "olaf": "Computer-Use Agent (Olaf)",
    "meeting-router": "Meeting Router",
}

DEFAULT_ANGIE_DELEGATION_ACK = (
    "Hey — got it. I'll start on this now and have Nikki check our codebase."
)


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


def _heuristic_stub_response(
    request: AgentRequest, active_voice_agent: str | None = None
) -> AgentResponse:
    """Local dev: approximate meeting-router listen vs respond."""
    words = request.mentioned_wake_words or [request.wake_word]
    direct, routed_to = is_direct_agent_call(request.utterance, words)

    if active_voice_agent and active_voice_agent != "angie":
        routed_to = active_voice_agent
        direct = True

    if not direct or not routed_to:
        return AgentResponse(
            text="",
            agent_name=AGENT_MAP["meeting-router"],
            routed_to=None,
            should_respond=False,
            reason="heuristic stub: mention only, keep listening",
        )

    # Angie decides to delegate — router sets routed_to nikki, not the orchestrator.
    if routed_to == "angie" and angie_should_delegate_to_nikki(request):
        return AgentResponse(
            text=DEFAULT_ANGIE_DELEGATION_ACK,
            agent_name=AGENT_MAP["angie"],
            routed_to="nikki",
            should_respond=True,
            reason="heuristic stub: Angie delegates to Nikki",
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


def _stub_response(request: AgentRequest, active_voice_agent: str | None = None) -> AgentResponse:
    mode = _router_mode()
    if mode == "listen":
        return _passthrough_listen_stub(request)
    return _heuristic_stub_response(request, active_voice_agent)


def _load_skill(rel_path: str) -> str:
    """Load a local SKILL.md so cloud agents work without a GitHub repo attached."""
    root = Path(__file__).resolve().parents[1]
    path = root / rel_path
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return f"(skill file not found: {rel_path})"


def _angie_ack_from_router(router: AgentResponse) -> str:
    """Angie's immediate line before Nikki runs — from router response_text."""
    raw = (router.text or "").strip()
    if raw and "NIKKI INCIDENT REPORT" not in raw:
        return raw
    return DEFAULT_ANGIE_DELEGATION_ACK


class OrchestratorClient:
    """
    Invoke the meeting-router agent with full meeting context.

    Teammate replaces the body of `invoke()` with Cursor Cloud Agent API
    when ROUTER_MODE=cloud.

    All spoken replies pass through SpeechEditorClient before TTS.
    """

    def __init__(self, active_voice_agent: str | None = None) -> None:
        self._active_voice_agent = (active_voice_agent or "").strip().lower() or None
        self._speech_editor = SpeechEditorClient()
        self._nikki = NikkiClient()
        self._olaf = OlafClient()
        self._last_router_response: AgentResponse | None = None

    async def _invoke_cloud_router(self, request: AgentRequest) -> AgentResponse:
        """Call the meeting-router Cursor Cloud Agent as a tool with try/except.

        Failures **never** propagate to the audio loop: we degrade to a
        keep-listening response and log the error. This is the "text request to
        the Cursor Cloud Agents API" the voice loop uses for every wake word.
        """
        meet_url = shared_meet_url()
        skill = _load_skill("agents/meeting-router/SKILL.md")
        prompt = (
            "You are the meeting-router cloud agent. Follow the skill below.\n\n"
            f"--- SKILL ---\n{skill}\n--- END SKILL ---\n\n"
            f"AgentRequest:\n{request.to_json()}\n\n"
            f"Shared Meet URL for every agent: {meet_url or '(not configured)'}\n\n"
            "Return the router JSON (action, routed_to, response_text, reason) only."
        )
        try:
            result = invoke_cursor_agent(
                prompt,
                auto_create_pr=False,
                repository=os.getenv("CURSOR_AGENTS_REPOSITORY") or None,
            )
        except Exception as exc:  # noqa: BLE001 — defensive: never crash Meet
            logger.exception("cursor cloud router raised unexpectedly")
            return AgentResponse(
                text="",
                agent_name=AGENT_MAP["meeting-router"],
                should_respond=False,
                reason=f"cloud router raised: {exc}",
            )

        if not result.ok:
            logger.warning("cursor cloud router failed: %s", result.error)
            return AgentResponse(
                text="",
                agent_name=AGENT_MAP["meeting-router"],
                should_respond=False,
                reason=f"cloud router error: {result.error}",
            )

        try:
            return parse_router_response(result.text, request)
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("cursor cloud router returned unparseable JSON: %s", exc)
            return AgentResponse(
                text="",
                agent_name=AGENT_MAP["meeting-router"],
                should_respond=False,
                reason=f"cloud router bad JSON: {exc}",
            )

    async def _dispatch_specialist(
        self, request: AgentRequest, response: AgentResponse
    ) -> AgentResponse:
        """Spawn specialist when meeting-router sets routed_to (not nikki — two-phase)."""
        target = response.routed_to or request.wake_word

        if target == "olaf":
            print(f"[{_ts()}] orchestrator → spawning Olaf (computer-use)")
            return await self._olaf.execute(request)
        return response

    async def complete_specialist(
        self, request: AgentRequest, target: str
    ) -> AgentResponse:
        """Run specialist work after Angie's immediate ack has been spoken."""
        if target == "nikki":
            print(f"[{_ts()}] orchestrator → Nikki (after Angie ack)")
            nikki = await self._nikki.execute(request)
            if not nikki.should_respond or not nikki.text:
                return nikki
            return AgentResponse(
                text=nikki.text,
                raw_text=nikki.raw_text or nikki.text,
                agent_name="Angie",
                routed_to="nikki",
                should_respond=True,
                reason=f"nikki follow-up: {nikki.reason}",
            )
        return AgentResponse(
            text="",
            agent_name=AGENT_MAP["meeting-router"],
            should_respond=False,
            reason=f"unknown specialist {target}",
        )

    async def deferred_angie_ack(self, request: AgentRequest) -> AgentResponse | None:
        """Speak the meeting-router's ack when angie-instant cloud did not."""
        router = self._last_router_response
        if not router or not router.should_respond:
            return None
        text = _angie_ack_from_router(router)
        if not text.strip():
            return None
        ack = AgentResponse(
            text=text,
            raw_text=text,
            agent_name="Angie",
            routed_to=router.routed_to,
            should_respond=True,
            reason="router ack fallback after angie-instant miss",
        )
        ack = await self._speech_editor.prepare(ack, request)
        print(f"[{_ts()}] angie router ack fallback → {ack.text!r}")
        return ack

    async def invoke(
        self, request: AgentRequest, *, skip_ack: bool = False
    ) -> AgentResponse:
        logger.info("[%s] agent.request %s", _ts(), request.summary_for_log())
        print(f"[{_ts()}] --- AgentRequest → meeting-router ---")
        print(request.to_json())
        print(f"[{_ts()}] ------------------------------------")

        mode = _router_mode()
        if mode == "cloud":
            response = await self._invoke_cloud_router(request)
        else:
            response = _stub_response(request, self._active_voice_agent)

        self._last_router_response = response

        if response.should_respond:
            if response.routed_to:
                print(f"[{_ts()}] meeting-router → routed_to={response.routed_to}")

            if response.routed_to == "nikki":
                if skip_ack:
                    print(f"[{_ts()}] angie instant ack pending — queuing Nikki")
                    return AgentResponse(
                        text="",
                        agent_name="Angie",
                        routed_to="nikki",
                        should_respond=False,
                        pending_specialist="nikki",
                        reason="nikki pending after instant ack",
                    )
                ack = AgentResponse(
                    text=_angie_ack_from_router(response),
                    raw_text=_angie_ack_from_router(response),
                    agent_name="Angie",
                    routed_to="nikki",
                    should_respond=True,
                    pending_specialist="nikki",
                    reason="angie immediate ack — Nikki runs after TTS",
                )
                ack = await self._speech_editor.prepare(ack, request)
                logger.info("[%s] angie ack (pending nikki) %s", _ts(), ack.summary_for_log())
                print(f"[{_ts()}] angie ack → {ack.text!r}")
                return ack

            response = await self._dispatch_specialist(request, response)

        if response.should_respond and response.text:
            response = await self._speech_editor.prepare(response, request)

        if response.should_respond and response.text:
            logger.info("[%s] agent.response %s", _ts(), response.summary_for_log())
            print(f"[{_ts()}] router → respond: {response.summary_for_log()}")
        else:
            reason = response.reason or "keep listening"
            print(f"[{_ts()}] router → listen: {reason}")

        return response
