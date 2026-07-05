"""Nikki code agent — finds and fixes bugs in the local mock-incident codebase."""

from __future__ import annotations

import importlib.util
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

from speech.agent_context import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

CHECKOUT_FILE = Path("app") / "checkout.py"
CHECKOUT_FIXED = Path("app") / "checkout_fixed.py"
INCIDENT_FILE = Path("INCIDENT.md")

BUGGY_TOTAL_ACCESS = 'cart["total"]'
FIXED_TOTAL_ACCESS = 'cart.get("total", 0)'


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def mock_incident_root() -> Path:
    override = os.getenv("MOCK_INCIDENT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "mock-incident"


@dataclass
class NikkiResult:
    status: str
    issue_found: bool
    issue_fixed: bool
    root_cause: str
    fix_applied: str
    response_text: str
    file_path: str


def _find_bug_line(source: str) -> int | None:
    for idx, line in enumerate(source.splitlines(), start=1):
        if BUGGY_TOTAL_ACCESS in line or "cart['total']" in line:
            return idx
        if FIXED_TOTAL_ACCESS in line or "cart.get('total'" in line:
            return idx
    return None


def _checkout_process_checkout(path: Path):
    spec = importlib.util.spec_from_file_location("mock_checkout", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.process_checkout


def _verify_empty_cart(path: Path) -> bool:
    try:
        fn = _checkout_process_checkout(path)
        fn({})
        return True
    except Exception:
        return False


def _build_report(
    *,
    issue_found: bool,
    issue_fixed: bool,
    root_cause: str,
    fix_applied: str,
    location: str,
) -> str:
    return (
        "NIKKI INCIDENT REPORT\n"
        f"ISSUE_FOUND: {'yes' if issue_found else 'no'}\n"
        f"ISSUE_FIXED: {'yes' if issue_fixed else 'no'}\n"
        f"ROOT_CAUSE: {root_cause}\n"
        f"FIX_APPLIED: {fix_applied}\n"
        f"LOCATION: {location}"
    )


def investigate_and_fix_local(request: AgentRequest) -> NikkiResult:
    root = mock_incident_root()
    checkout_path = root / CHECKOUT_FILE
    fixed_path = root / CHECKOUT_FIXED

    if not checkout_path.is_file():
        return NikkiResult(
            status="failed",
            issue_found=False,
            issue_fixed=False,
            root_cause="mock checkout service not found on disk",
            fix_applied="",
            response_text="NIKKI INCIDENT REPORT\nISSUE_FOUND: no\nISSUE_FIXED: no\nROOT_CAUSE: checkout.py missing",
            file_path=str(checkout_path),
        )

    source = checkout_path.read_text(encoding="utf-8")
    bug_line = _find_bug_line(source)
    location = f"{CHECKOUT_FILE.as_posix()}:{bug_line or '?'}"

    already_fixed = FIXED_TOTAL_ACCESS in source or "cart.get('total'" in source
    has_bug = BUGGY_TOTAL_ACCESS in source or "cart['total']" in source

    root_cause = (
        "checkout assumed every cart has a total field — empty carts raised KeyError"
    )

    if already_fixed and not has_bug:
        verified = _verify_empty_cart(checkout_path)
        return NikkiResult(
            status="completed",
            issue_found=True,
            issue_fixed=False,
            root_cause=root_cause,
            fix_applied="guard already present — cart.get('total', 0)",
            response_text=_build_report(
                issue_found=True,
                issue_fixed=False,
                root_cause=root_cause,
                fix_applied=f"already patched in place; empty cart check={'pass' if verified else 'fail'}",
                location=location,
            ),
            file_path=str(checkout_path.relative_to(root)),
        )

    if not has_bug:
        return NikkiResult(
            status="completed",
            issue_found=False,
            issue_fixed=False,
            root_cause="could not locate the empty-cart KeyError pattern in checkout.py",
            fix_applied="",
            response_text=_build_report(
                issue_found=False,
                issue_fixed=False,
                root_cause="no matching bug pattern in checkout.py",
                fix_applied="none",
                location=location,
            ),
            file_path=str(checkout_path.relative_to(root)),
        )

    # Apply fix in place
    if fixed_path.is_file():
        patched = fixed_path.read_text(encoding="utf-8")
    else:
        patched = source.replace(BUGGY_TOTAL_ACCESS, FIXED_TOTAL_ACCESS)
        patched = patched.replace("cart['total']", "cart.get('total', 0)")

    checkout_path.write_text(patched, encoding="utf-8")
    verified = _verify_empty_cart(checkout_path)
    fix_applied = (
        "replaced cart['total'] with cart.get('total', 0) in checkout.py"
        if verified
        else "wrote fix but empty-cart verification failed"
    )

    logger.info(
        "nikki fix applied path=%s line=%s verified=%s",
        checkout_path,
        bug_line,
        verified,
    )

    return NikkiResult(
        status="completed" if verified else "failed",
        issue_found=True,
        issue_fixed=verified,
        root_cause=root_cause,
        fix_applied=fix_applied,
        response_text=_build_report(
            issue_found=True,
            issue_fixed=verified,
            root_cause=root_cause,
            fix_applied=fix_applied,
            location=location,
        ),
        file_path=str(checkout_path.relative_to(root)),
    )


class NikkiClient:
    """Find and fix bugs under mock-incident/ — local files only."""

    async def execute(self, request: AgentRequest) -> AgentResponse:
        print(f"[{_ts()}] nikki: investigating + fixing at {mock_incident_root()}")
        result = investigate_and_fix_local(request)
        should_respond = bool(result.response_text.strip())
        return AgentResponse(
            text=result.response_text,
            raw_text=result.response_text,
            agent_name="Code Agent (Nikki)",
            routed_to="nikki",
            should_respond=should_respond,
            reason=(
                f"nikki: found={result.issue_found} fixed={result.issue_fixed} "
                f"({result.file_path})"
            ),
        )
