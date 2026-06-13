"""URL validation helpers for user-supplied links."""

from __future__ import annotations

from urllib.parse import urlparse


def sanitize_http_url(url: str | None) -> str | None:
    """Return url only if it uses http or https with a host; otherwise None."""
    if not url or not isinstance(url, str):
        return None
    trimmed = url.strip()
    if not trimmed:
        return None
    if not trimmed.startswith(("http://", "https://")):
        if "." in trimmed and not trimmed.startswith("."):
            trimmed = f"https://{trimmed}"
    parsed = urlparse(trimmed)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return trimmed
    return None
