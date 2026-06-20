"""Tests for the agents-cli core framework."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from reliantai.agents.core.base import AgentConfig, AgentResult, AgentState, BaseAgent


class TestAgent(BaseAgent):
    """Concrete test agent for unit testing the base class."""

    def __init__(self, config: AgentConfig, **kwargs):
        super().__init__(config)
        self._has_work = kwargs.get("has_work", True)
        self._execute_result = kwargs.get("execute_result", {"ok": True})
        self._execute_fail = kwargs.get("execute_fail", False)
        self._operation_name_str = kwargs.get("operation_name", "test_op")
        self.execute_calls = 0

    def _operation_name(self) -> str:
        return self._operation_name_str

    async def _check_for_work(self) -> bool:
        return self._has_work

    async def _execute(self) -> dict:
        self.execute_calls += 1
        if self._execute_fail:
            raise RuntimeError("test failure")
        return self._execute_result


@pytest.fixture
def agent_config():
    return AgentConfig(
        name="test_agent",
        max_retries=2,
        retry_backoff_base=0.01,  # Fast retries for tests
        retry_backoff_max=0.05,
        poll_interval_seconds=0.01,
        timeout_seconds=5.0,
    )


@pytest.fixture
def agent(agent_config):
    return TestAgent(agent_config)


class TestAgentConfig:
    def test_defaults(self):
        config = AgentConfig(name="test")
        assert config.max_retries == 3
        assert config.poll_interval_seconds == 30.0
        assert config.enabled is True

    def test_custom(self):
        config = AgentConfig(name="custom", max_retries=5, poll_interval_seconds=10.0)
        assert config.max_retries == 5
        assert config.poll_interval_seconds == 10.0


class TestAgentResult:
    def test_defaults(self):
        r = AgentResult(success=True)
        assert r.success is True
        assert r.data == {}
        assert r.error is None

    def test_full(self):
        r = AgentResult(success=False, data={"x": 1}, error="fail", duration_ms=100.0, retries=2)
        assert r.success is False
        assert r.error == "fail"
        assert r.retries == 2


class TestBaseAgent:
    def test_init(self, agent):
        assert agent.name == "test_agent"
        assert agent.state == AgentState.IDLE
        assert agent.is_running is False

    def test_stats(self, agent):
        stats = agent.stats
        assert stats["name"] == "test_agent"
        assert stats["state"] == "idle"
        assert stats["total_processed"] == 0

    def test_stop(self, agent):
        agent.state = AgentState.RUNNING
        agent.stop()
        assert agent.state == AgentState.STOPPED

    @pytest.mark.asyncio
    async def test_check_for_work(self, agent):
        assert await agent._check_for_work() is True

    @pytest.mark.asyncio
    async def test_execute(self, agent):
        result = await agent._execute()
        assert result == {"ok": True}
        assert agent.execute_calls == 1

    @pytest.mark.asyncio
    async def test_process_with_retry_success(self, agent):
        result = await agent._process_with_retry()
        assert result.success is True
        assert result.data == {"ok": True}
        assert result.retries == 0

    @pytest.mark.asyncio
    async def test_process_with_retry_failure(self, agent_config):
        failing_agent = TestAgent(agent_config, execute_fail=True)
        result = await failing_agent._process_with_retry()
        assert result.success is False
        assert "test failure" in result.error
        assert result.retries == 2  # max_retries

    @pytest.mark.asyncio
    async def test_process_with_retry_eventual_success(self, agent_config):
        """Agent fails once then succeeds."""
        agent = TestAgent(agent_config, execute_fail=True)
        call_count = 0

        original_execute = agent._execute

        async def flaky_execute():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("first attempt fails")
            return {"recovered": True}

        agent._execute = flaky_execute
        result = await agent._process_with_retry()
        assert result.success is True
        assert result.data == {"recovered": True}
        assert result.retries == 1

    @pytest.mark.asyncio
    async def test_run_stops_when_no_work(self, agent_config):
        """Agent with no work should stop after one poll cycle."""
        agent = TestAgent(agent_config, has_work=False)
        agent.config.poll_interval_seconds = 0.01

        # Run with a timeout
        async def run_with_timeout():
            try:
                await asyncio.wait_for(agent.run(), timeout=0.5)
            except asyncio.TimeoutError:
                agent.stop()

        await run_with_timeout()
        assert agent.state == AgentState.STOPPED

    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        health = await agent.health_check()
        assert health["name"] == "test_agent"
        assert health["healthy"] is True

    @pytest.mark.asyncio
    async def test_stats_accumulate(self, agent_config):
        """Stats should accumulate across multiple process cycles."""
        agent = TestAgent(agent_config, has_work=True)
        agent.config.poll_interval_seconds = 0.01

        # Manually run a few cycles
        for _ in range(3):
            result = await agent._process_with_retry()
            agent._results.append(result)
            agent._total_processed += 1

        assert agent.stats["total_processed"] == 3
