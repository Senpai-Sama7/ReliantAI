"""
Base agent class with autonomous loop, error recovery, and telemetry.
"""

from __future__ import annotations

import asyncio
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core import Telemetry, get_logger


class AgentState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentResult:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0
    retries: int = 0


@dataclass
class AgentConfig:
    name: str
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    retry_backoff_max: float = 60.0
    poll_interval_seconds: float = 30.0
    max_concurrent_tasks: int = 5
    timeout_seconds: float = 300.0
    enabled: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all autonomous agents.

    Features:
    - Autonomous run loop with configurable poll interval
    - Automatic retry with exponential backoff
    - Verbose telemetry logging for every operation
    - Graceful shutdown via stop() method
    - Health check endpoint
    - State tracking
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.IDLE
        self.logger = get_logger(f"agents.{config.name}")
        self._stop_event = asyncio.Event()
        self._results: list[AgentResult] = []
        self._total_processed = 0
        self._total_errors = 0
        self._total_retries = 0
        self._last_run: float = 0
        self._last_error: str | None = None

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def is_running(self) -> bool:
        return self.state == AgentState.RUNNING

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "total_processed": self._total_processed,
            "total_errors": self._total_errors,
            "total_retries": self._total_retries,
            "last_run": self._last_run,
            "last_error": self._last_error,
            "recent_results": len(self._results),
        }

    def stop(self) -> None:
        """Signal the agent to stop after the current operation."""
        self.logger.info("agent_stopping", agent=self.name)
        self._stop_event.set()
        self.state = AgentState.STOPPED

    async def run(self) -> None:
        """
        Main autonomous loop. Runs until stop() is called.
        Polls for work, processes it, and sleeps between iterations.
        """
        self.state = AgentState.RUNNING
        self.logger.info("agent_started", agent=self.name)

        while not self._stop_event.is_set():
            try:
                self._last_run = time.time()
                has_work = await self._check_for_work()

                if not has_work:
                    self.state = AgentState.WAITING
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(),
                            timeout=self.config.poll_interval_seconds,
                        )
                    except asyncio.TimeoutError:
                        continue
                    continue

                self.state = AgentState.RUNNING
                result = await self._process_with_retry()
                self._results.append(result)
                if len(self._results) > 100:
                    self._results = self._results[-100:]

                if result.success:
                    self._total_processed += 1
                else:
                    self._total_errors += 1
                    self._last_error = result.error

            except asyncio.CancelledError:
                self.logger.info("agent_cancelled", agent=self.name)
                break
            except Exception as e:
                self._total_errors += 1
                self._last_error = str(e)
                self.logger.error(
                    "agent_loop_error",
                    agent=self.name,
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.config.retry_backoff_max,
                    )
                except asyncio.TimeoutError:
                    continue

        self.state = AgentState.STOPPED
        self.logger.info("agent_stopped", agent=self.name, stats=self.stats)

    async def _process_with_retry(self) -> AgentResult:
        """Process work with automatic retry and telemetry."""
        start = time.monotonic()
        last_error = None

        for attempt in range(1, self.config.max_retries + 1):
            try:
                with Telemetry(
                    operation=self._operation_name(),
                    agent=self.name,
                    attempt=attempt,
                ):
                    data = await asyncio.wait_for(
                        self._execute(),
                        timeout=self.config.timeout_seconds,
                    )

                duration = (time.monotonic() - start) * 1000
                self._total_retries += attempt - 1
                return AgentResult(
                    success=True,
                    data=data,
                    duration_ms=duration,
                    retries=attempt - 1,
                )

            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.config.timeout_seconds}s"
                self.logger.warning(
                    "operation_timeout",
                    agent=self.name,
                    attempt=attempt,
                    timeout=self.config.timeout_seconds,
                )
            except Exception as e:
                last_error = str(e)
                self.logger.warning(
                    "operation_error",
                    agent=self.name,
                    attempt=attempt,
                    error=str(e),
                )

            if attempt < self.config.max_retries:
                wait_time = min(
                    self.config.retry_backoff_base ** attempt,
                    self.config.retry_backoff_max,
                )
                self.logger.info("retrying", agent=self.name, attempt=attempt, wait_seconds=wait_time)
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=wait_time)
                    return AgentResult(
                        success=False,
                        error="Stopped during retry wait",
                        duration_ms=(time.monotonic() - start) * 1000,
                        retries=attempt,
                    )
                except asyncio.TimeoutError:
                    continue

        duration = (time.monotonic() - start) * 1000
        self._total_retries += self.config.max_retries
        return AgentResult(
            success=False,
            error=last_error or "Max retries exceeded",
            duration_ms=duration,
            retries=self.config.max_retries,
        )

    @abstractmethod
    async def _check_for_work(self) -> bool:
        """Check if there is work to process. Return True if yes."""
        ...

    @abstractmethod
    async def _execute(self) -> dict[str, Any]:
        """Execute the main work. Called with retry and telemetry."""
        ...

    @abstractmethod
    def _operation_name(self) -> str:
        """Return the operation name for telemetry."""
        ...

    async def health_check(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "healthy": self.state in (AgentState.RUNNING, AgentState.WAITING, AgentState.IDLE),
            "stats": self.stats,
        }
