"""Nikki sales agent — creates Jira tickets when sales reports bugs."""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from speech.agent_context import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

NIKKI_AGENT_NAME = "Sales Agent (Nikki)"
TICKETS_PATH = Path(__file__).resolve().parent.parent / "data" / "jira_tickets.json"
DEMO_FIXTURE = (
    Path(__file__).resolve().parent.parent / "orders" / "demo" / "jira-ticket.json"
)

_BUG_REPORT = re.compile(
    r"\b(?:log|file|raise|create|open|report|track)\b.*\b(?:jira|ticket|issue|bug)\b"
    r"|\b(?:jira|ticket|issue|bug)\b.*\b(?:log|file|raise|create|open|report|track)\b"
    r"|\b(?:isn't|is not|doesn't|does not|not)\s+working\b"
    r"|\bbroken\b"
    r"|\bbug\b",
    re.I,
)

_STATUS_CHECK = re.compile(
    r"\b(?:status|update|progress)\b.*\b(?:ticket|issue|jira|bug)\b"
    r"|\b(?:ticket|issue)\b.*\b(?:status|update|progress|fixed|resolved)\b"
    r"|\bis\s+(?:it|that|the\s+\w+)\s+fixed\b",
    re.I,
)

_ORDER_SAVER = re.compile(r"\border\s*saver\b|\bsave\s+(?:order|button)\b", re.I)


def _ts() -> str:
    return time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


def nikki_mode() -> str:
    return os.getenv("NIKKI_MODE", "stub").strip().lower()


@dataclass
class JiraTicket:
    key: str
    summary: str
    description: str
    status: str
    priority: str
    reporter: str
    labels: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str | None = None
    resolution: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _load_tickets() -> list[dict]:
    if not TICKETS_PATH.exists():
        return []
    try:
        data = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_tickets(tickets: list[dict]) -> None:
    TICKETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TICKETS_PATH.write_text(json.dumps(tickets, indent=2), encoding="utf-8")


def _next_key(tickets: list[dict]) -> str:
    project = os.getenv("JIRA_PROJECT_KEY", "RAISE")
    numbers = []
    for t in tickets:
        key = str(t.get("key", ""))
        if key.startswith(f"{project}-"):
            try:
                numbers.append(int(key.split("-", 1)[1]))
            except ValueError:
                pass
    n = max(numbers, default=46) + 1
    return f"{project}-{n}"


def _extract_summary(utterance: str) -> str:
    if _ORDER_SAVER.search(utterance):
        return "Order Saver — Save order button does nothing"
    cleaned = re.sub(r"\bnikki\b", "", utterance, flags=re.I)
    cleaned = re.sub(r"\b(?:log|file|raise|create|open|report|track)\b.*\bjira\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,!?-")
    if len(cleaned) > 80:
        cleaned = cleaned[:77] + "..."
    return cleaned or "Customer-reported bug from sales meeting"


def _extract_description(request: AgentRequest, summary: str) -> str:
    lines = [
        f"Reported during live meeting by sales.",
        "",
        f"Summary: {summary}",
        "",
        f"Triggering utterance: {request.utterance}",
        "",
        "Meeting context (recent):",
        request.recent_transcript or "(none)",
    ]
    return "\n".join(lines)


def _demo_ticket_dict() -> dict | None:
    if not DEMO_FIXTURE.exists():
        return None
    try:
        data = json.loads(DEMO_FIXTURE.read_text(encoding="utf-8"))
        t = data.get("ticket", {})
        return {
            "key": t.get("key", "RAISE-47"),
            "summary": t.get("summary", ""),
            "description": t.get("description", ""),
            "status": t.get("status", "Done"),
            "priority": t.get("priority", "High"),
            "reporter": t.get("reporter", "Alex Morgan (Sales)"),
            "labels": t.get("labels", []),
            "created_at": t.get("created", datetime.now(timezone.utc).isoformat()),
            "resolved_at": t.get("resolved"),
            "resolution": (t.get("resolution") or {}).get("summary"),
        }
    except (json.JSONDecodeError, OSError):
        return None


def _find_order_saver_ticket(tickets: list[dict]) -> dict | None:
    for t in tickets:
        summary = str(t.get("summary", "")).lower()
        if "order saver" in summary or "save order" in summary or "save button" in summary:
            return t
    return None


def _create_stub_ticket(request: AgentRequest) -> JiraTicket:
    tickets = _load_tickets()

    if _ORDER_SAVER.search(request.utterance):
        existing = _find_order_saver_ticket(tickets)
        if existing:
            return JiraTicket(**{k: existing[k] for k in JiraTicket.__dataclass_fields__ if k in existing})

        demo = _demo_ticket_dict()
        summary = demo["summary"] if demo else "Order Saver — Save order button does nothing"
        description = demo["description"] if demo else _extract_description(request, summary)
        ticket = JiraTicket(
            key=_next_key(tickets) if not demo else demo["key"],
            summary=summary,
            description=description,
            status="Open",
            priority="High",
            reporter=os.getenv("JIRA_REPORTER", "Alex Morgan (Sales)"),
            labels=["order-saver", "demo", "customer-reported"],
        )
        tickets.append(ticket.to_dict())
        _save_tickets(tickets)
        return ticket

    summary = _extract_summary(request.utterance)
    ticket = JiraTicket(
        key=_next_key(tickets),
        summary=summary,
        description=_extract_description(request, summary),
        status="Open",
        priority="High" if re.search(r"\bdemo\b|\bcustomer\b|\blocking\b", request.utterance, re.I) else "Medium",
        reporter=os.getenv("JIRA_REPORTER", "Alex Morgan (Sales)"),
        labels=["sales-reported", "meeting"],
    )
    tickets.append(ticket.to_dict())
    _save_tickets(tickets)
    return ticket


def _create_jira_api_ticket(request: AgentRequest) -> JiraTicket:
    host = os.getenv("JIRA_HOST", "").rstrip("/")
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "")
    project = os.getenv("JIRA_PROJECT_KEY", "RAISE")

    if not all([host, email, token]):
        logger.warning("JIRA_* env vars incomplete — falling back to stub")
        return _create_stub_ticket(request)

    summary = _extract_summary(request.utterance)
    description = _extract_description(request, summary)
    priority = "High" if re.search(r"\bdemo\b|\bcustomer\b|\blocking\b", request.utterance, re.I) else "Medium"

    payload = {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
            "issuetype": {"name": os.getenv("JIRA_ISSUE_TYPE", "Bug")},
            "labels": ["sales-reported", "meeting"],
        }
    }

    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    req = urllib.request.Request(
        f"{host}/rest/api/3/issue",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        key = data.get("key", _next_key(_load_tickets()))
        ticket = JiraTicket(
            key=key,
            summary=summary,
            description=description,
            status="Open",
            priority=priority,
            reporter=os.getenv("JIRA_REPORTER", "Alex Morgan (Sales)"),
            labels=["sales-reported", "meeting"],
        )
        tickets = _load_tickets()
        tickets.append(ticket.to_dict())
        _save_tickets(tickets)
        return ticket
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        logger.error("Jira API create failed: %s", exc)
        return _create_stub_ticket(request)


def _create_ticket(request: AgentRequest) -> JiraTicket:
    if nikki_mode() == "jira":
        return _create_jira_api_ticket(request)
    return _create_stub_ticket(request)


def _reply_for_create(ticket: JiraTicket) -> str:
    if ticket.status.lower() in {"done", "resolved", "closed"}:
        resolution = ticket.resolution or "already fixed"
        return (
            f"I found existing ticket {ticket.key} — {ticket.summary}. "
            f"It's already {ticket.status.lower()}: {resolution}."
        )
    return (
        f"Logged {ticket.key} — {ticket.summary}. "
        f"Marked {ticket.priority} priority. I'll ping engineering."
    )


def _reply_for_status(request: AgentRequest) -> str:
    tickets = _load_tickets()
    ticket = None

    if _ORDER_SAVER.search(request.utterance):
        ticket = _find_order_saver_ticket(tickets)

    if ticket is None and tickets:
        ticket = tickets[-1]

    if ticket is None:
        demo = _demo_ticket_dict()
        ticket = demo

    if ticket is None:
        return "I don't see any open tickets yet. Want me to log one?"

    key = ticket.get("key", "UNKNOWN")
    status = str(ticket.get("status", "Open"))
    summary = ticket.get("summary", "the reported issue")

    if status.lower() in {"done", "resolved", "closed"}:
        resolution = ticket.get("resolution") or "engineering confirmed the fix"
        return f"{key} is {status.lower()} — {resolution}. You should be good to rerun the demo."

    return f"{key} is {status} — {summary}. Engineering is on it."


class NikkiClient:
    """Sales agent: file bugs in Jira when sales reports them in a meeting."""

    async def invoke(self, request: AgentRequest) -> AgentResponse:
        utterance = request.utterance
        print(f"[{_ts()}] --- AgentRequest → Nikki (sales) ---")
        print(request.to_json())
        print(f"[{_ts()}] -----------------------------------")

        if _BUG_REPORT.search(utterance):
            ticket = _create_ticket(request)
            text = _reply_for_create(ticket)
            reason = f"nikki: created/found Jira ticket {ticket.key}"
            print(f"[{_ts()}] nikki → Jira: {ticket.key} ({ticket.status})")
        elif _STATUS_CHECK.search(utterance):
            text = _reply_for_status(request)
            reason = "nikki: ticket status lookup"
        else:
            text = "I'm here. Tell me what's broken and I'll log it in Jira."
            reason = "nikki: general sales assist"

        return AgentResponse(
            text=text,
            agent_name=NIKKI_AGENT_NAME,
            routed_to="nikki",
            should_respond=True,
            reason=reason,
        )
