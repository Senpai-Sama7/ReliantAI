"""
ReliantAI Event Bus HTTP client — single place for /publish semantics.

The Event Bus requires ``Authorization: Bearer <EVENT_BUS_API_KEY>`` on mutating
routes when ``EVENT_BUS_API_KEY`` is set (see ``integration/event-bus/event_bus.py``).

Environment:
  EVENT_BUS_URL       — base URL, default http://localhost:8081
  EVENT_BUS_API_KEY   — bearer token for /publish, /event/{id}, /dlq, etc.
"""

from __future__ import annotations

import os
from typing import Any, Mapping
from urllib.parse import urlparse

import httpx
import requests

DEFAULT_EVENT_BUS_URL = "http://localhost:8081"


def get_event_bus_url() -> str:
    return os.getenv("EVENT_BUS_URL", DEFAULT_EVENT_BUS_URL).rstrip("/")


def get_event_bus_auth_headers() -> dict[str, str]:
    key = (os.getenv("EVENT_BUS_API_KEY") or "").strip()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def publish_request_headers(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    h: dict[str, str] = {"Content-Type": "application/json"}
    h.update(get_event_bus_auth_headers())
    if extra:
        h.update(extra)
    return h


def should_verify_tls(url: str) -> bool:
    """Localhost HTTP is common in dev; verify TLS for everything else."""
    try:
        parsed = urlparse(url)
    except Exception:
        return True
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "http" and host in ("127.0.0.1", "localhost", "::1"):
        return False
    return True


def publish_sync(
    body: dict[str, Any],
    *,
    timeout: float = 5.0,
    verify: bool | None = None,
):
    """POST /publish using ``requests``. Returns ``requests.Response``."""
    base = get_event_bus_url()
    url = f"{base}/publish"
    if verify is None:
        verify = should_verify_tls(url)
    return requests.post(
        url,
        json=body,
        headers=publish_request_headers(),
        timeout=timeout,
        verify=verify,
    )


async def publish_async(
    body: dict[str, Any],
    *,
    timeout: float = 5.0,
    verify: bool | None = None,
):
    """POST /publish using ``httpx``. Returns ``httpx.Response``."""
    base = get_event_bus_url()
    url = f"{base}/publish"
    if verify is None:
        verify = should_verify_tls(url)
    async with httpx.AsyncClient(timeout=timeout, verify=verify) as client:
        return await client.post(
            url,
            json=body,
            headers=publish_request_headers(),
        )


def get_event_sync(
    event_id: str,
    *,
    timeout: float = 5.0,
    verify: bool | None = None,
):
    """GET /event/{event_id} (requires API key when bus is fail-closed)."""
    base = get_event_bus_url()
    url = f"{base}/event/{event_id}"
    if verify is None:
        verify = should_verify_tls(url)
    return requests.get(
        url,
        headers=publish_request_headers(),
        timeout=timeout,
        verify=verify,
    )
