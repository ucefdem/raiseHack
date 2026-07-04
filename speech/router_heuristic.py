"""Heuristic stand-in for meeting-router during local dev (no cloud agent yet)."""

from __future__ import annotations

import re

_CLAUSE_SPLIT = re.compile(r"[.?!]+\s*")

_GREETING_LEAD = re.compile(
    r"^(?:hey|hi|hello|ok|okay|yo|so|well|now)[,\s]+",
    re.IGNORECASE,
)

# Future/planning — mention only, not an active call yet
_LISTEN_PATTERNS = [
    re.compile(r"\bhand(?:ing)?\s+over\s+to\s+", re.I),
    re.compile(r"\b(?:going|about)\s+to\s+ask\s+", re.I),
    re.compile(r"\b(?:talked|spoke)\s+about\s+", re.I),
    re.compile(r"\bsaid\s+", re.I),
    re.compile(r"\bmentioned\s+", re.I),
    re.compile(r"\b(?:asking|ask)\s+\w+\s+to\s+be\s+activated\b", re.I),
]


def _clause_direct_ask(clause: str, word: str) -> bool:
    lowered = clause.lower().strip().rstrip(".,!?")
    if not lowered or not re.search(rf"\b{re.escape(word)}\b", lowered):
        return False

    if any(p.search(lowered) for p in _LISTEN_PATTERNS):
        return False

    if _GREETING_LEAD.match(lowered) and re.search(rf"\b{re.escape(word)}\b", lowered):
        return True

    tokens = re.findall(r"[a-z']+", lowered)
    if tokens and tokens[0] == word:
        return True
    if (
        len(tokens) >= 2
        and tokens[0] in {"hey", "hi", "hello", "ok", "okay", "yo", "so", "well", "now"}
        and tokens[1] == word
    ):
        return True

    if re.search(rf"\b{re.escape(word)}\s*,?\s*(?:could|can)\s*you", lowered):
        return True
    if re.search(rf"\b{re.escape(word)}\s*,?\s*please\b", lowered):
        return True
    if re.search(rf"(?:what|how)\s+about\s+{re.escape(word)}\b", lowered):
        return True
    if re.search(rf"(?:please\s+)?(?:call|ask)\s+{re.escape(word)}\b", lowered):
        return True
    if re.search(rf"\basking\s+{re.escape(word)}\b", lowered):
        return True
    if re.search(rf"\bactivate\s+{re.escape(word)}\b", lowered):
        return True
    if re.search(rf"\b{re.escape(word)}\b.*\b(?:pull\s+up|open|show|check|get|find)\b", lowered):
        return True

    return False


def is_direct_agent_call(utterance: str, wake_words: list[str]) -> tuple[bool, str | None]:
    """
    Return whether the utterance is a direct agent call and which agent to route to.

    Uses the last direct-ask clause when multiple agents are named.
    """
    lowered = utterance.lower().strip()
    clauses = [c.strip() for c in _CLAUSE_SPLIT.split(lowered) if c.strip()] or [lowered]

    best_pos = -1
    best_word: str | None = None
    cursor = 0
    for clause in clauses:
        clause_start = lowered.find(clause, cursor)
        if clause_start < 0:
            clause_start = cursor
        cursor = clause_start + len(clause)

        for word in wake_words:
            if not _clause_direct_ask(clause, word):
                continue
            pos = clause_start + clause.find(word)
            if pos >= best_pos:
                best_pos = pos
                best_word = word

    return best_word is not None, best_word


STUB_REPLIES = {
    "angie": "I'm here. I'll coordinate that for you.",
    "nikki": "I'm here. I'll check on that for you.",
    "olaf": "I'm here. Pulling that up now.",
}
