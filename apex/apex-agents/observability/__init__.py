# apex-agents/observability/__init__.py
from observability.langfuse_client import get_trace_callback, langfuse_enabled

__all__ = ["get_trace_callback", "langfuse_enabled"]
