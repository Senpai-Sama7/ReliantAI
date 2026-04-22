#!/usr/bin/env python3
"""
Orchestrator v3 Enhancements
=============================

Critical improvements to add to system-prompt-review:

1. Conditional Dependencies (on="completed"|"failed"|"any")
2. Result Store (parent→child payload injection)
3. Token Bucket Rate Limiting
4. Middleware Chain (pre/post/error hooks)
5. Workflow Controller (pause/resume/cancel by workflow_id)
6. Recurring Scheduler (max_instances guard)
7. Circuit Breaker Persistence
8. Quiescence Latch (stop_when_empty race fix)
9. Priority Inheritance
10. Prometheus Text Export

Apply these to the existing orchestrator.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Awaitable
import time
import json
import sqlite3
import asyncio


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 1: Conditional Dependencies
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class Dependency:
    """
    Typed dependency with conditional activation.
    
    on="completed" → runs only if parent succeeds (default)
    on="failed"    → runs only if parent fails/times out/DLQ
    on="any"       → runs regardless of parent outcome (cleanup)
    """
    task_id: str
    on: str = "completed"  # "completed" | "failed" | "any"
    
    @classmethod
    def coerce(cls, val: str | dict | Dependency) -> Dependency:
        if isinstance(val, cls): return val
        if isinstance(val, str): return cls(task_id=val, on="completed")
        if isinstance(val, dict): return cls(task_id=val["task_id"], on=val.get("on", "completed"))
        raise TypeError(f"Cannot coerce {type(val)} to Dependency")
    
    def to_dict(self) -> Dict[str, str]:
        return {"task_id": self.task_id, "on": self.on}
    
    def is_satisfied_by(self, status: str) -> bool:
        """Check if dependency condition is met by parent status."""
        if self.on == "completed":
            return status == "completed"
        if self.on == "failed":
            return status in {"failed", "timed_out", "dead_letter"}
        if self.on == "any":
            return status in {"completed", "failed", "cancelled", "timed_out", "dead_letter"}
        return False


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 2: Result Store
# ═════════════════════════════════════════════════════════════════════════════

class ResultStore:
    """
    Persist executor outputs to SQLite, inject into child task.payload["__results__"].
    
    Separates input (payload) from output (result) — clean data flow.
    """
    
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._bootstrap()
    
    def _bootstrap(self):
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS task_results (
                    task_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    stored_at REAL NOT NULL
                )
            """)
    
    def store(self, task_id: str, result: Dict[str, Any]):
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO task_results VALUES (?,?,?)",
                (task_id, json.dumps(result, default=str), time.time())
            )
    
    def get_many(self, task_ids: List[str]) -> Dict[str, Any]:
        if not task_ids: return {}
        ph = ",".join("?" * len(task_ids))
        rows = self._conn.execute(
            f"SELECT task_id, result_json FROM task_results WHERE task_id IN ({ph})",
            task_ids
        ).fetchall()
        return {r[0]: json.loads(r[1]) for r in rows}
    
    def inject_parent_results(self, task: Any, tasks: Dict[str, Any]):
        """Inject parent results into task.payload["__results__"] at scheduling time."""
        parent_ids = [dep.task_id if hasattr(dep, 'task_id') else dep 
                      for dep in task.dependencies]
        if not parent_ids: return
        results = self.get_many(parent_ids)
        if results:
            task.payload["__results__"] = results


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 3: Token Bucket Rate Limiter
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class TokenBucket:
    """
    Leaky-bucket rate limiter. Allows burst up to capacity, then enforces rate.
    
    Usage:
        limiter = TokenBucket(rate=10.0, capacity=20.0)  # 10/s, burst 20
        if not limiter.consume():
            raise RateLimitError()
    """
    rate: float      # tokens/second
    capacity: float  # max burst
    _tokens: float = field(init=False, default=0.0)
    _last_ts: float = field(init=False, default=0.0)
    
    def __post_init__(self):
        self._tokens = self.capacity
        self._last_ts = time.monotonic()
    
    def consume(self, tokens: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self._last_ts
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_ts = now
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False
    
    def wait_time_s(self, tokens: float = 1.0) -> float:
        """Seconds until tokens available."""
        deficit = tokens - self._tokens
        return max(0.0, deficit / self.rate)


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 4: Middleware Chain
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class MiddlewareContext:
    """Context passed to middleware: before/after/error phases."""
    task: Any
    phase: str  # "before" | "after" | "error"
    result: Optional[Dict] = None
    error: Optional[Exception] = None
    duration_s: Optional[float] = None


MiddlewareFn = Callable[[MiddlewareContext], Awaitable[None]]


class MiddlewareChain:
    """
    Intercept task execution lifecycle.
    
    Use cases: auth injection, tracing, cost tracking, validation.
    """
    
    def __init__(self, log=None):
        self._middleware: List[MiddlewareFn] = []
        self._log = log
    
    def use(self, fn: MiddlewareFn) -> MiddlewareFn:
        self._middleware.append(fn)
        return fn
    
    async def run_before(self, task: Any):
        ctx = MiddlewareContext(task=task, phase="before")
        for mw in self._middleware:
            await self._safe(mw, ctx, task.trace_id)
    
    async def run_after(self, task: Any, result: Dict, duration_s: float):
        ctx = MiddlewareContext(task=task, phase="after", result=result, duration_s=duration_s)
        for mw in self._middleware:
            await self._safe(mw, ctx, task.trace_id)
    
    async def run_error(self, task: Any, error: Exception):
        ctx = MiddlewareContext(task=task, phase="error", error=error)
        for mw in self._middleware:
            await self._safe(mw, ctx, task.trace_id)
    
    async def _safe(self, fn: MiddlewareFn, ctx: MiddlewareContext, trace_id: str):
        try:
            await fn(ctx)
        except Exception as exc:
            if self._log:
                self._log.warning("middleware.error", trace_id=trace_id, error=str(exc))


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 5: Recurring Scheduler
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class RecurringSpec:
    """
    Recurring task specification with max_instances guard.
    
    Prevents pileup: if previous instance hasn't finished, skip next tick.
    """
    prefix: str
    type: str
    interval_s: float
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 8
    timeout_s: float = 30.0
    max_retries: int = 1
    max_instances: int = 1
    next_run_at: float = field(default_factory=time.time)
    _active: int = field(default=0, repr=False)


class RecurringScheduler:
    """
    Interval-based task submission with max_instances guard.
    
    Integration:
        scheduler.tick(completed_task_id)  # on completion
        scheduler.check_and_submit(tasks)  # each loop iteration
    """
    
    def __init__(self, submit_fn: Callable):
        self._specs: Dict[str, RecurringSpec] = {}
        self._submit = submit_fn
    
    def schedule(self, spec: RecurringSpec):
        self._specs[spec.prefix] = spec
    
    def tick(self, completed_task_id: str):
        """Decrement active count on task completion."""
        for spec in self._specs.values():
            if completed_task_id.startswith(spec.prefix + "_"):
                spec._active = max(0, spec._active - 1)
    
    def check_and_submit(self, current_tasks: Dict) -> List:
        now = time.time()
        submitted = []
        for spec in self._specs.values():
            if now < spec.next_run_at: continue
            if spec._active >= spec.max_instances: continue
            task_id = f"{spec.prefix}_{int(now * 1000)}"
            if task_id in current_tasks: continue
            
            task = self._submit(
                task_id, type=spec.type, payload=dict(spec.payload),
                priority=spec.priority, timeout_s=spec.timeout_s,
                max_retries=spec.max_retries
            )
            spec._active += 1
            spec.next_run_at = now + spec.interval_s
            submitted.append(task)
        return submitted


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 6: Workflow Controller
# ═════════════════════════════════════════════════════════════════════════════

class WorkflowController:
    """
    Bulk operations on workflow_id-grouped tasks.
    
    Operations: cancel, pause, resume by workflow_id.
    """
    
    def __init__(self, tasks: Dict, store, log, bus):
        self._tasks = tasks
        self._store = store
        self._log = log
        self._bus = bus
    
    def cancel_workflow(self, workflow_id: str) -> int:
        n = 0
        for task in self._tasks.values():
            if task.workflow_id != workflow_id: continue
            if task.status.value == "pending":
                task.status = type(task.status)("cancelled")
                task.completed_at = time.time()
                self._store.upsert(task)
                n += 1
        self._log.info("workflow.cancelled", workflow_id=workflow_id, count=n)
        return n
    
    def pause_workflow(self, workflow_id: str) -> int:
        n = 0
        for task in self._tasks.values():
            if task.workflow_id != workflow_id: continue
            if task.status.value == "pending":
                task.status = type(task.status)("paused")
                self._store.upsert(task)
                n += 1
        self._log.info("workflow.paused", workflow_id=workflow_id, count=n)
        return n
    
    def resume_workflow(self, workflow_id: str) -> int:
        n = 0
        for task in self._tasks.values():
            if task.workflow_id != workflow_id: continue
            if task.status.value == "paused":
                task.status = type(task.status)("pending")
                self._store.upsert(task)
                n += 1
        self._log.info("workflow.resumed", workflow_id=workflow_id, count=n)
        return n


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 7: Priority Inheritance
# ═════════════════════════════════════════════════════════════════════════════

def apply_priority_inheritance(task: Any, tasks: Dict, store):
    """
    Propagate child priority upward through dependency chain.
    
    Solves priority inversion: critical task blocked on background task.
    """
    if not task.dependencies: return
    
    stack = [dep.task_id if hasattr(dep, 'task_id') else dep 
             for dep in task.dependencies]
    visited = set()
    
    while stack:
        dep_id = stack.pop()
        if dep_id in visited: continue
        visited.add(dep_id)
        
        dep_task = tasks.get(dep_id)
        if dep_task and dep_task.priority > task.priority:
            dep_task.priority = task.priority
            store.upsert(dep_task)
            stack.extend(d.task_id if hasattr(d, 'task_id') else d 
                        for d in dep_task.dependencies)


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 8: Prometheus Text Export
# ═════════════════════════════════════════════════════════════════════════════

def prometheus_text_export(metrics_registry) -> str:
    """
    Generate Prometheus exposition format text.
    
    Endpoint: GET /metrics/prometheus
    Content-Type: text/plain; version=0.0.4
    """
    lines = []
    
    # Counters
    for key, val in sorted(metrics_registry._counters.items()):
        name = key.split("{")[0] if "{" in key else key
        lines.append(f"# TYPE orchestrator_{name}_total counter")
        lines.append(f"orchestrator_{key}_total {val}")
    
    # Gauges
    for key, val in sorted(metrics_registry._gauges.items()):
        name = key.split("{")[0] if "{" in key else key
        lines.append(f"# TYPE orchestrator_{name} gauge")
        lines.append(f"orchestrator_{key} {val}")
    
    # Histograms (as summaries)
    for key, vals in sorted(metrics_registry._hists.items()):
        if not vals: continue
        name = key.split("{")[0] if "{" in key else key
        s = sorted(vals)
        lines.append(f"# TYPE orchestrator_{name} summary")
        
        for q, idx in [(0.5, int(0.50*len(s))), (0.95, int(0.95*len(s))), (0.99, int(0.99*len(s)))]:
            lines.append(f'orchestrator_{name}{{quantile="{q}"}} {s[idx]}')
        lines.append(f"orchestrator_{name}_count {len(s)}")
        lines.append(f"orchestrator_{name}_sum {sum(s)}")
    
    return "\n".join(lines) + "\n"


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 9: Quiescence Latch
# ═════════════════════════════════════════════════════════════════════════════

class QuiescenceLatch:
    """
    Stability window for stop_when_empty.
    
    Requires 50ms of no new tasks before declaring batch complete.
    Closes executor→add_task race condition.
    """
    
    def __init__(self, window_s: float = 0.050):
        self.window_s = window_s
        self._start: Optional[float] = None
    
    def reset(self):
        self._start = None
    
    def check(self, all_terminal: bool) -> bool:
        """Returns True if quiescent for window_s."""
        if not all_terminal:
            self._start = None
            return False
        
        if self._start is None:
            self._start = time.monotonic()
            return False
        
        return (time.monotonic() - self._start) >= self.window_s


# ═════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT 10: Circuit Breaker Persistence
# ═════════════════════════════════════════════════════════════════════════════

def save_circuit_breaker(conn: sqlite3.Connection, cb: Any):
    """Persist circuit breaker state to SQLite."""
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS circuit_breakers (
                task_type TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                consecutive_failures INTEGER NOT NULL,
                probe_successes INTEGER NOT NULL,
                tripped_at REAL,
                last_success_at REAL
            )
        """)
        conn.execute("""
            INSERT INTO circuit_breakers VALUES (?,?,?,?,?,?)
            ON CONFLICT(task_type) DO UPDATE SET
                state=excluded.state,
                consecutive_failures=excluded.consecutive_failures,
                probe_successes=excluded.probe_successes,
                tripped_at=excluded.tripped_at,
                last_success_at=excluded.last_success_at
        """, (cb.task_type, cb.state.name, cb.consecutive_failures,
              cb.probe_successes, cb.tripped_at, 
              getattr(cb, 'last_success_at', None)))


def load_circuit_breakers(conn: sqlite3.Connection) -> Dict:
    """Load persisted circuit breaker states."""
    try:
        rows = conn.execute("SELECT * FROM circuit_breakers").fetchall()
        return {r[0]: {
            "state": r[1],
            "consecutive_failures": r[2],
            "probe_successes": r[3],
            "tripped_at": r[4],
            "last_success_at": r[5]
        } for r in rows}
    except sqlite3.OperationalError:
        return {}
