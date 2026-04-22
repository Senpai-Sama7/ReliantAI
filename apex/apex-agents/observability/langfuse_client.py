# apex-agents/observability/langfuse_client.py
from __future__ import annotations
import os
from typing import Any

LANGFUSE_ENABLED = (
    os.getenv("LANGFUSE_HOST")
    and os.getenv("LANGFUSE_PUBLIC_KEY")
    and os.getenv("LANGFUSE_SECRET_KEY")
)


def langfuse_enabled() -> bool:
    return bool(LANGFUSE_ENABLED)


def get_trace_callback(trace_id: str, agent_name: str) -> Any:
    if not langfuse_enabled():
        return None
    try:
        from langfuse import Langfuse

        langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "https://langfuse.com"),
        )
        trace = langfuse.trace(id=trace_id, name=agent_name)
        return trace.get_cb()
    except Exception:
        return None
