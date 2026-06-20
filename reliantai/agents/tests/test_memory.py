"""Tests for the agents-cli memory module."""

from __future__ import annotations

import os
import tempfile

import pytest

from reliantai.agents.core.memory import AgentMemory


@pytest.fixture
def memory():
    """Create a temporary memory database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    mem = AgentMemory(db_path=db_path)
    yield mem
    os.unlink(db_path)


class TestAgentMemory:
    def test_remember_and_recall(self, memory):
        memory.remember("test_agent", "key1", "value1")
        result = memory.recall("test_agent", "key1")
        assert result == "value1"

    def test_recall_missing(self, memory):
        assert memory.recall("test_agent", "nonexistent") is None

    def test_remember_overwrite(self, memory):
        memory.remember("test_agent", "key1", "v1")
        memory.remember("test_agent", "key1", "v2")
        assert memory.recall("test_agent", "key1") == "v2"

    def test_recall_all(self, memory):
        memory.remember("agent1", "k1", "v1")
        memory.remember("agent1", "k2", "v2")
        memory.remember("agent2", "k3", "v3")

        all_mem = memory.recall_all("agent1")
        assert all_mem == {"k1": "v1", "k2": "v2"}

        all_mem2 = memory.recall_all("agent2")
        assert all_mem2 == {"k3": "v3"}

    def test_log_event(self, memory):
        memory.log_event("agent1", "test_event", {"data": "value"})
        events = memory.get_events("agent1")
        assert len(events) == 1
        assert events[0]["type"] == "test_event"
        assert events[0]["data"] == {"data": "value"}

    def test_get_events_filtered(self, memory):
        memory.log_event("agent1", "type_a", {"x": 1})
        memory.log_event("agent1", "type_b", {"x": 2})
        memory.log_event("agent1", "type_a", {"x": 3})

        type_a = memory.get_events("agent1", event_type="type_a")
        assert len(type_a) == 2

        type_b = memory.get_events("agent1", event_type="type_b")
        assert len(type_b) == 1

    def test_get_events_limit(self, memory):
        for i in range(10):
            memory.log_event("agent1", "evt", {"i": i})

        events = memory.get_events("agent1", limit=5)
        assert len(events) == 5

    def test_isolation_between_agents(self, memory):
        memory.remember("agent1", "key", "val1")
        memory.remember("agent2", "key", "val2")

        assert memory.recall("agent1", "key") == "val1"
        assert memory.recall("agent2", "key") == "val2"

    def test_remember_complex_value(self, memory):
        value = {"nested": {"list": [1, 2, 3]}, "str": "hello"}
        memory.remember("agent1", "complex", value)
        result = memory.recall("agent1", "complex")
        assert result == value
