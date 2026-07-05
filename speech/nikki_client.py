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

BUGGY_PATTERNS = ('cart["total"]', "cart['total']")
FIXED_MARKERS = ('cart.get("total", 0)', "cart.get('total', 0)")


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


def _source_has_bug(source: str) -> bool:
    return any(p in source for p in BUGGY_PATTERNS)


def _source_is_fixed(source: str) -> bool:
    return any(m in source for m in FIXED_MARKERS)


def _find_line(source: str, needle: str) -> int | None:
    for idx, line in enumerate(source.splitlines(), start=1):
        if needle in line:
            return idx
    return None


def _load_process_checkout(path: Path):
    """Load checkout.py from disk — fresh module name so Python never serves a stale cache."""
    module_name = f"mock_checkout_{abs(hash(str(path.resolve())))}_{path.stat().st_mtime_ns}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.process_checkout


def _verify_empty_cart(path: Path) -> bool:
    try:
        fn = _load_process_checkout(path)
        result = fn({})
        return isinstance(result, dict) and result.get("amount_due") == 0.0
    except Exception as exc:
        logger.warning("empty-cart verify failed for %s: %s", path, exc)
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


def _patch_source(source: str, fixed_path: Path) -> str:
    if fixed_path.is_file():
        return fixed_path.read_text(encoding="utf-8")
    patched = source
    for buggy in BUGGY_PATTERNS:
        patched = patched.replace(buggy, 'cart.get("total", 0)')
    return patched


def investigate_and_fix_local(request: AgentRequest) -> NikkiResult:
    root = mock_incident_root()
    checkout_path = (root / CHECKOUT_FILE).resolve()
    fixed_path = root / CHECKOUT_FIXED

    if not checkout_path.is_file():
        return NikkiResult(
            status="failed",
            issue_found=False,
            issue_fixed=False,
            root_cause="mock checkout service not found on disk",
            fix_applied="",
            response_text=_build_report(
                issue_found=False,
                issue_fixed=False,
                root_cause="checkout.py missing",
                fix_applied="none",
                location=str(checkout_path),
            ),
            file_path=str(checkout_path),
        )

    source = checkout_path.read_text(encoding="utf-8")
    root_cause = (
        "checkout assumed every cart has a total field — empty carts raised KeyError"
    )

    if _source_has_bug(source):
        bug_line = _find_line(source, BUGGY_PATTERNS[0]) or _find_line(source, BUGGY_PATTERNS[1])
        location = f"{CHECKOUT_FILE.as_posix()}:{bug_line or '?'}"

        patched = _patch_source(source, fixed_path)
        checkout_path.write_text(patched, encoding="utf-8")
        print(f"[{_ts()}] nikki: wrote fix → {checkout_path}")

        on_disk = checkout_path.read_text(encoding="utf-8")
        verified = _verify_empty_cart(checkout_path) and _source_is_fixed(on_disk)
        if not verified:
            print(f"[{_ts()}] nikki: WARNING fix verification failed for {checkout_path}")

        fix_applied = (
            f"updated {checkout_path.name} in place — cart.get('total', 0)"
            if verified
            else f"wrote {checkout_path.name} but verification failed"
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
            file_path=str(checkout_path),
        )

    if _source_is_fixed(source):
        bug_line = _find_line(source, FIXED_MARKERS[0]) or _find_line(source, FIXED_MARKERS[1])
        location = f"{CHECKOUT_FILE.as_posix()}:{bug_line or '?'}"
        verified = _verify_empty_cart(checkout_path)
        return NikkiResult(
            status="completed",
            issue_found=True,
            issue_fixed=False,
            root_cause=root_cause,
            fix_applied="no change needed — fix already present on disk",
            response_text=_build_report(
                issue_found=True,
                issue_fixed=False,
                root_cause=root_cause,
                fix_applied=f"already fixed in {checkout_path.name}; empty cart check={'pass' if verified else 'fail'}",
                location=location,
            ),
            file_path=str(checkout_path),
        )

    return NikkiResult(
        status="completed",
        issue_found=False,
        issue_fixed=False,
        root_cause="could not locate the empty-cart bug pattern in checkout.py",
        fix_applied="none",
        response_text=_build_report(
            issue_found=False,
            issue_fixed=False,
            root_cause="no matching bug pattern in checkout.py",
            fix_applied="none",
            location=str(checkout_path),
        ),
        file_path=str(checkout_path),
    )


class NikkiClient:
    """Find and fix bugs under mock-incident/ — local files only."""

    async def execute(self, request: AgentRequest) -> AgentResponse:
        root = mock_incident_root()
        print(f"[{_ts()}] nikki: investigating + fixing at {root}")
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
                f"path={result.file_path}"
            ),
        )
