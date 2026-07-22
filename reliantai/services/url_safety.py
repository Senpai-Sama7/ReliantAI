"""URL validation helpers for user-supplied links and server-side fetches."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


_BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "metadata",
    }
)


def sanitize_http_url(url: str | None) -> str | None:
    """Return url only if it uses http or https with a host; otherwise None.

    Suitable for display/href filtering. Does NOT block private IPs —
    use is_public_http_url() before server-side fetches.
    """
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


def is_public_http_url(url: str | None) -> bool:
    """True only for http(s) URLs that resolve to non-private, non-link-local hosts.

    Use before any server-side outbound fetch (SSRF guard).
    """
    cleaned = sanitize_http_url(url)
    if not cleaned:
        return False

    parsed = urlparse(cleaned)
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or host in _BLOCKED_HOSTS or host.endswith(".localhost"):
        return False

    # Reject credentials-in-URL (user:pass@host)
    if parsed.username or parsed.password:
        return False

    try:
        # Literal IP in hostname
        addr = ipaddress.ip_address(host)
        return not (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
        )
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False

    for info in infos:
        raw = info[4][0]
        try:
            addr = ipaddress.ip_address(raw)
        except ValueError:
            continue
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
        ):
            return False
    return True
