"""Pytest config for event-bus tests.

The event_bus service is fail-closed: endpoints require a valid
EVENT_BUS_API_KEY bearer token. For in-process tests we:

1. Seed EVENT_BUS_API_KEY so the module-level config reads a real value.
2. Override the auth dependency so tests don't need to carry Authorization
   headers on every call.

Both steps run before any test module in this directory is collected,
because pytest loads conftest.py prior to importing test files.
"""

import os

os.environ.setdefault("EVENT_BUS_API_KEY", "test-api-key")

import pytest  # noqa: E402 -- import order matters (env var must be set first)

from event_bus import app, require_event_bus_api_key  # noqa: E402


@pytest.fixture(autouse=True)
def _bypass_event_bus_auth():
    """Short-circuit the API-key gate for the duration of each test."""
    app.dependency_overrides[require_event_bus_api_key] = lambda: True
    try:
        yield
    finally:
        app.dependency_overrides.pop(require_event_bus_api_key, None)
