#!/usr/bin/env python3
"""Smoke-test Cursor Cloud Agents API from worker/.env.

    cd worker && uv run python verify_cursor.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from speech.agent_context import AgentRequest
from speech.angie_instant_client import AngieInstantClient, instant_mode
from speech.cursor_cloud_client import invoke_cursor_agent
from speech.orchestrator import OrchestratorClient


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def check_me() -> bool:
    key = os.getenv("CURSOR_API_KEY", "").strip()
    if not key:
        print("FAIL: CURSOR_API_KEY is not set in worker/.env")
        return False
    auth = base64.b64encode(f"{key}:".encode()).decode()
    req = urllib.request.Request(
        "https://api.cursor.com/v1/me",
        headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: /v1/me — {exc}")
        return False
    print(f"OK: API key valid ({data.get('apiKeyName', 'unknown')}, {data.get('userEmail', '')})")
    return True


def check_agent_ping() -> bool:
    result = invoke_cursor_agent(
        "Reply with exactly: CURSOR API OK",
        auto_create_pr=False,
        wait_for_result=True,
        poll_timeout_s=60.0,
    )
    if not result.ok:
        print(f"FAIL: agent invoke — {result.error}")
        return False
    preview = (result.text or "").strip()[:120] or "(empty)"
    print(f"OK: agent invoke — agent={result.agent_id} text={preview!r}")
    return bool(result.text.strip())


async def check_angie_instant() -> bool:
    req = AgentRequest(
        wake_word="angie",
        mentioned_wake_words=["angie"],
        utterance=(
            "Angie, a customer says checkout crashes when the cart is empty. "
            "Can you take a look?"
        ),
        meeting_transcript="",
        recent_transcript="",
    )
    out = await AngieInstantClient().generate(req)
    if not out.ok or not out.text.strip():
        print(f"FAIL: angie-instant — {out.error}")
        return False
    print(f"OK: angie-instant — delegate={out.delegate_to} text={out.text!r}")
    return True


async def check_cloud_router() -> bool:
    os.environ["ROUTER_MODE"] = "cloud"
    req = AgentRequest(
        wake_word="angie",
        mentioned_wake_words=["angie"],
        utterance="Angie, a customer says checkout crashes when the cart is empty.",
        meeting_transcript="",
        recent_transcript="",
    )
    out = await OrchestratorClient(active_voice_agent="angie").invoke(req)
    if not out.should_respond:
        print(f"FAIL: cloud router listen — {out.reason}")
        return False
    print(f"OK: cloud router respond — routed_to={out.routed_to}")
    print(f"    TTS preview: {out.text[:160]}...")
    return True


def main() -> None:
    _load_dotenv()
    print("=== Cursor Cloud Agents verify ===\n")
    steps = [
        ("API key", check_me),
        ("Agent ping (poll)", check_agent_ping),
    ]
    ok = all(fn() for _, fn in steps)
    print()
    if ok:
        print("Running angie-instant test (parallel path, may take ~10–35s)...")
        ok = asyncio.run(check_angie_instant())
    print()
    if ok:
        print("Running cloud meeting-router test (may take ~15–60s)...")
        ok = asyncio.run(check_cloud_router())
    print()
    if ok:
        print("All checks passed. Set ROUTER_MODE=cloud in worker/.env and restart the worker.")
    else:
        print("Some checks failed — keep ROUTER_MODE=heuristic until fixed.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
