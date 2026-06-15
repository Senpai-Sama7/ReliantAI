"""SMS compliance helpers (TCPA opt-out detection)."""

from __future__ import annotations

import re

STOP_PHRASES = frozenset(
    {"stop", "unsubscribe", "quit", "cancel", "end", "no more", "opt out", "remove me"}
)
STOP_WORD_BOUNDARY = frozenset({"stop", "unsubscribe", "quit", "cancel", "end"})


def is_stop_request(body: str) -> bool:
    normalized = body.strip().lower()
    if normalized in STOP_PHRASES:
        return True
    for word in STOP_WORD_BOUNDARY:
        if re.search(rf"\b{re.escape(word)}\b", normalized):
            return True
    for phrase in ("no more", "opt out", "remove me"):
        if phrase in normalized:
            return True
    return False
