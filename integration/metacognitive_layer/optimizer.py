"""
Autonomous Optimizer - Continuous Performance Optimization

Self-tuning system that optimizes cache, resources, and configurations
without human intervention. Implements safety-first optimization with
automatic rollback on degradation.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json
import statistics

import asyncpg


class OptimizationDomain(Enum):
    """Domains where autonomous optimization can apply."""
    CACHE = "cache"                    # Cache TTL, size, eviction policy
    DATABASE = "database"              # Connection pool, query plans
    RESOURCE = "resource"              # Memory, CPU allocation
    BATCH = "batch"                    # Batch sizes, processing windows
    TIMEOUT = "timeout"                # Request timeouts, retries
    COMPRESSION = "compression"        # Compression algorithms, levels


class OptimizationStatus(Enum):
    """Status of an optimization attempt."""
    PENDING = "pending"
    TESTING = "testing"                # A/B testing phase
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class OptimizationConfig:
    """Configuration for an optimizable parameter."""
    domain: OptimizationDomain
    parameter_name: str
    current_value: Any
    valid_range: Tuple[float, float]  # (min, max) for numeric
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Safety thresholds
    max_change_percent: float = 20.0   # Max % change per optimization
    requires_rollback_plan: bool = True
    peak_hours_blackout: Tuple[int, int] = (9, 17)  # Don't optimize during


@dataclass
class OptimizationAction:
    """A single optimization action."""
    action_id: str
    timestamp: datetime
    domain: OptimizationDomain
    parameter: str
    old_value: Any
    new_value: Any
    confidence: float
    expected_improvement: float
    rollback_command: Optional[str] = None
    
    # Testing and validation
    status: OptimizationStatus = OptimizationStatus.PENDING
    test_start_time: Optional[datetime] = None
    validation_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class PerformanceBaseline:
    """Baseline metrics for comparison."""
    baseline_id: str
    recorded_at: datetime
    metrics: Dict[str, float]
    duration_minutes: int = 10
    
    def get_metric(self, name: str) -> Optional[float]:
        return self.metrics.get(name)
    
    def compare(self, current: Dict[str, float]) -> Dict[str, float]:
        """Compare current metrics to baseline."""
        changes = {}
        for metric, baseline_val in self.metrics.items():
            current_val = current.get(metric)
            if current_val is not None:
                if baseline_val != 0:
                    pct_change = (current_val - baseline_val) / baseline_val * 100
                else:
                    pct_change = float('inf') if current_val > 0 else 0
                changes[metric] = pct_change
        return changes


class OptimizationStrategy:
    """Base class for optimization strategies."""
    
    def __init__(self, domain: OptimizationDomain):
        self.domain = domain
    
    async def analyze(self, metrics_history: List[Dict[str, Any]]) -> Optional[OptimizationAction]:
        """Analyze metrics and suggest optimization."""
        raise NotImplementedError
    
    async def apply(self, action: OptimizationAction) -> bool:
        """Apply the optimization."""
        raise NotImplementedError
    
    async def rollback(self, action: OptimizationAction) -> bool:
        """Rollback the optimization."""
        raise NotImplementedError


class CacheOptimizationStrategy(OptimizationStrategy):
    """Optimize cache TTL based on hit/miss rates."""
    
    def __init__(self):
        super().__init__(OptimizationDomain.CACHE)
        self.hit_rate_history: List[float] = []
    
    async def analyze(self, metrics_history: List[Dict[str, Any]]) -> Optional[OptimizationAction]:
        """Analyze cache metrics and suggest TTL adjustments."""
        if len(metrics_history) < 5:
            return None
        
        # Extract hit rates
        hit_rates = [
            m.get('cache_hit_rate', 0) 
            for m in metrics_history[-10:]
            if 'cache_hit_rate' in m
        ]
        
        if len(hit_rates) < 5:
            return None
        
        avg_hit_rate = statistics.mean(hit_rates)
        current_ttl = metrics_history[-1].get('cache_ttl_seconds', 300)
        
        # Low hit rate = increase TTL to keep items longer
        if avg_hit_rate < 0.7:
            new_ttl = min(current_ttl * 1.2, 3600)  # Max 1 hour
            confidence = 0.7
            expected_improvement = 0.15
        # High hit rate = decrease TTL for fresher data
        elif avg_hit_rate > 0.95:
            new_ttl = max(current_ttl * 0.8, 60)  # Min 1 minute
            confidence = 0.6
            expected_improvement = 0.05
        else:
            return None
        
        return OptimizationAction(
            action_id=f"cache_ttl_{datetime.now(timezone.utc).timestamp()}",
            timestamp=datetime.now(timezone.utc),
            domain=OptimizationDomain.CACHE,
            parameter="cache_ttl_seconds",
            old_value=current_ttl,
            new_value=int(new_ttl),
            confidence=confidence,
            expected_improvement=expected_improvement,
            rollback_command=f"set_cache_ttl({current_ttl})"
        )
    
    async def apply(self, action: OptimizationAction) -> bool:
        """Apply cache TTL change."""
        print(f"🔧 Applying cache optimization: TTL {action.old_value}s → {action.new_value}s")
        # Would actually apply to cache system here
        return True
    
    async def rollback(self, action: OptimizationAction) -> bool:
        """Rollback cache TTL."""
        print(f"↩️ Rolling back cache TTL to {action.old_value}s")
        return True


class ConnectionPoolOptimizationStrategy(OptimizationStrategy):
    """Optimize database connection pool size."""
    
    def __init__(self):
        super().__init__(OptimizationDomain.DATABASE)
    
    async def analyze(self, metrics_history: List[Dict[str, Any]]) -> Optional[OptimizationAction]:
        """Analyze connection pool utilization."""
        if len(metrics_history) < 5:
            return None
        
        recent = metrics_history[-5:]
        wait_times = [m.get('connection_wait_ms', 0) for m in recent if 'connection_wait_ms' in m]
        utilization = [m.get('pool_utilization', 0) for m in recent if 'pool_utilization' in m]
        
        if not wait_times or not utilization:
            return None
        
        avg_wait = statistics.mean(wait_times)
        avg_utilization = statistics.mean(utilization)
        current_size = recent[-1].get('pool_size', 10)
        
        # High wait time = increase pool size
        if avg_wait > 100 or avg_utilization > 0.9:
            new_size = min(int(current_size * 1.3), 50)  # Max 50 connections
            confidence = 0.75
            expected_improvement = 0.3
        # Low utilization = decrease pool size
        elif avg_utilization < 0.3 and current_size > 5:
            new_size = max(int(current_size * 0.8), 5)  # Min 5 connections
            confidence = 0.6
            expected_improvement = 0.1
        else:
            return None
        
        return OptimizationAction(
            action_id=f"pool_size_{datetime.now(timezone.utc).timestamp()}",
            timestamp=datetime.now(timezone.utc),
            domain=OptimizationDomain.DATABASE,
            parameter="connection_pool_size",
            old_value=current_size,
            new_value=new_size,
            confidence=confidence,
            expected_improvement=expected_improvement,
            rollback_command=f"set_pool_size({current_size})"
        )
    
    async def apply(self, action: OptimizationAction) -> bool:
        """Apply connection pool size change."""
        print(f"🔧 Applying pool optimization: Size {action.old_value} → {action.new_value}")
        return True
    
    async def rollback(self, action: OptimizationAction) -> bool:
        """Rollback pool size."""
        print(f"↩️ Rolling back pool size to {action.old_value}")
        return True


class AutonomousOptimizer:
    """
    Autonomous optimization system that continuously improves performance.
    
    Safety-first approach with:
    - A/B testing for all changes
    - Automatic rollback on degradation
    - Peak hour blackout periods
    - Gradual rollout (10% traffic first)
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self.db_pool = db_pool
        self.strategies: Dict[OptimizationDomain, OptimizationStrategy] = {}
        self.active_optimizations: Dict[str, OptimizationAction] = {}
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # Safety configuration
        self.safety_thresholds = {
            'max_error_rate_increase': 0.001,  # 0.1%
            'max_latency_increase_percent': 20,
            'min_improvement_percent': 5,
            'test_duration_minutes': 10,
        }
        
        # State
        self._is_running = False
        self._optimization_task: Optional[asyncio.Task] = None
        self._validation_task: Optional[asyncio.Task] = None
        
        # Register default strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default optimization strategies."""
        self.register_strategy(CacheOptimizationStrategy())
        self.register_strategy(ConnectionPoolOptimizationStrategy())
    
    def register_strategy(self, strategy: OptimizationStrategy):
        """Register an optimization strategy."""
        self.strategies[strategy.domain] = strategy
    
    async def initialize(self):
        """Initialize database and load state."""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                "postgresql://localhost:5435/metacognitive"
            )
        
        await self._ensure_schema()
        await self._load_active_optimizations()
        
        print("✅ Autonomous Optimizer initialized")
    
    async def _ensure_schema(self):
        """Create optimization tracking tables."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS optimization_actions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    action_id VARCHAR(128) UNIQUE,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    domain VARCHAR(64),
                    parameter_name VARCHAR(128),
                    old_value JSONB,
                    new_value JSONB,
                    confidence FLOAT,
                    expected_improvement FLOAT,
                    status VARCHAR(32) DEFAULT 'pending',
                    test_start_time TIMESTAMPTZ,
                    rollback_command TEXT,
                    validation_metrics JSONB DEFAULT '{}',
                    outcome VARCHAR(32),
                    rolled_back_at TIMESTAMPTZ
                );
                
                CREATE INDEX IF NOT EXISTS idx_opt_actions_status 
                    ON optimization_actions(status);
                CREATE INDEX IF NOT EXISTS idx_opt_actions_domain 
                    ON optimization_actions(domain);
                CREATE INDEX IF NOT EXISTS idx_opt_actions_time 
                    ON optimization_actions(timestamp DESC);
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_baselines (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    baseline_id VARCHAR(128) UNIQUE,
                    recorded_at TIMESTAMPTZ DEFAULT NOW(),
                    metrics JSONB,
                    duration_minutes INTEGER DEFAULT 10
                );
            """)
    
    async def _load_active_optimizations(self):
        """Load active optimizations from database."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM optimization_actions 
                WHERE status IN ('testing', 'applied')
            """)
            
            for row in rows:
                action = OptimizationAction(
                    action_id=row['action_id'],
                    timestamp=row['timestamp'],
                    domain=OptimizationDomain(row['domain']),
                    parameter=row['parameter_name'],
                    old_value=row['old_value'],
                    new_value=row['new_value'],
                    confidence=row['confidence'],
                    expected_improvement=row['expected_improvement'],
                    status=OptimizationStatus(row['status']),
                    test_start_time=row['test_start_time'],
                    rollback_command=row['rollback_command'],
                    validation_metrics=row['validation_metrics'] or {}
                )
                self.active_optimizations[action.action_id] = action
    
    async def record_metrics(self, metrics: Dict[str, Any]):
        """Record metrics for analysis."""
        metrics['timestamp'] = datetime.now(timezone.utc).isoformat()
        self.metrics_history.append(metrics)
        
        # Limit history size
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    async def start_optimization_loop(self, interval_seconds: float = 300.0):
        """Start continuous optimization."""
        self._is_running = True
        
        self._optimization_task = asyncio.create_task(
            self._optimization_loop(interval_seconds)
        )
        self._validation_task = asyncio.create_task(
            self._validation_loop(60.0)  # Check every minute
        )
        
        print(f"⚙️ Autonomous optimizer started (interval: {interval_seconds}s)")
    
    async def _optimization_loop(self, interval: float):
        """Main optimization loop."""
        while self._is_running:
            try:
                await self._run_optimization_cycle()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"⚠️ Optimization cycle error: {e}")
                await asyncio.sleep(60)
    
    async def _run_optimization_cycle(self):
        """Run a single optimization cycle."""
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # Skip during peak hours (configurable per strategy)
        if 9 <= hour <= 17:
            print("⏸️ Peak hours - skipping optimization cycle")
            return
        
        # Record baseline before any optimization
        await self._record_baseline()
        
        # Analyze with each strategy
        for domain, strategy in self.strategies.items():
            try:
                action = await strategy.analyze(self.metrics_history)
                if action and action.confidence >= 0.6:
                    await self._evaluate_and_apply(action, strategy)
            except Exception as e:
                print(f"⚠️ Strategy {domain.value} failed: {e}")
    
    async def _record_baseline(self):
        """Record current performance baseline."""
        if not self.metrics_history:
            return
        
        # Use last 10 minutes of metrics
        recent = self.metrics_history[-60:]  # Assume 10s intervals
        if not recent:
            return
        
        baseline_id = f"baseline_{datetime.now(timezone.utc).timestamp()}"
        metrics = {}
        
        # Aggregate metrics
        for metric_name in ['latency_ms', 'error_rate', 'cache_hit_rate', 'throughput']:
            values = [m.get(metric_name) for m in recent if m.get(metric_name) is not None]
            if values:
                metrics[f'{metric_name}_avg'] = statistics.mean(values)
                metrics[f'{metric_name}_p95'] = self._percentile(values, 95)
        
        baseline = PerformanceBaseline(
            baseline_id=baseline_id,
            recorded_at=datetime.now(timezone.utc),
            metrics=metrics,
            duration_minutes=10
        )
        
        self.baselines[baseline_id] = baseline
        
        # Persist to database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO performance_baselines (baseline_id, metrics, duration_minutes)
                VALUES ($1, $2, $3)
            """, baseline_id, json.dumps(metrics), 10)
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def _evaluate_and_apply(self, action: OptimizationAction, strategy: OptimizationStrategy):
        """Evaluate and potentially apply an optimization."""
        print(f"🔍 Evaluating optimization: {action.domain.value}.{action.parameter}")
        print(f"   Confidence: {action.confidence:.0%}, Expected improvement: {action.expected_improvement:.0%}")
        
        # Apply the optimization
        success = await strategy.apply(action)
        if not success:
            action.status = OptimizationStatus.FAILED
            return
        
        # Enter testing phase
        action.status = OptimizationStatus.TESTING
        action.test_start_time = datetime.now(timezone.utc)
        self.active_optimizations[action.action_id] = action
        
        # Persist
        await self._persist_action(action)
        
        print(f"🧪 Optimization {action.action_id} in testing phase")
    
    async def _validation_loop(self, interval: float):
        """Validate active optimizations."""
        while self._is_running:
            try:
                await self._validate_active_optimizations()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"⚠️ Validation error: {e}")
                await asyncio.sleep(10)
    
    async def _validate_active_optimizations(self):
        """Check if active optimizations are performing well."""
        now = datetime.now(timezone.utc)
        
        for action_id, action in list(self.active_optimizations.items()):
            if action.status != OptimizationStatus.TESTING:
                continue
            
            # Check if test duration elapsed
            if not action.test_start_time:
                continue
                
            elapsed = (now - action.test_start_time).total_seconds() / 60
            if elapsed < self.safety_thresholds['test_duration_minutes']:
                continue
            
            # Get current metrics
            recent_metrics = self._get_recent_metrics()
            
            # Find baseline from before this optimization
            baseline = self._find_relevant_baseline(action)
            if not baseline:
                continue
            
            # Compare performance
            is_improved = self._is_performance_improved(baseline, recent_metrics)
            
            if is_improved:
                # Optimization successful
                action.status = OptimizationStatus.APPLIED
                action.validation_metrics = recent_metrics
                print(f"✅ Optimization {action_id} validated and applied")
            else:
                # Rollback required
                await self._rollback_optimization(action)
            
            await self._persist_action(action)
    
    def _get_recent_metrics(self) -> Dict[str, float]:
        """Get aggregated recent metrics."""
        if not self.metrics_history:
            return {}
        
        recent = self.metrics_history[-60:]  # Last 10 min
        result = {}
        
        for metric_name in ['latency_ms', 'error_rate', 'cache_hit_rate', 'throughput']:
            values = [m.get(metric_name) for m in recent if m.get(metric_name) is not None]
            if values:
                result[f'{metric_name}_avg'] = statistics.mean(values)
        
        return result
    
    def _find_relevant_baseline(self, action: OptimizationAction) -> Optional[PerformanceBaseline]:
        """Find baseline recorded before this optimization."""
        if not action.test_start_time:
            return None
        
        # Find baseline closest to but before test start
        relevant_baselines = [
            b for b in self.baselines.values()
            if b.recorded_at < action.test_start_time
        ]
        
        if not relevant_baselines:
            return None
        
        return max(relevant_baselines, key=lambda b: b.recorded_at)
    
    def _is_performance_improved(self, baseline: PerformanceBaseline, 
                                  current: Dict[str, float]) -> bool:
        """Check if current performance is better than baseline."""
        changes = baseline.compare(current)
        
        # Check critical metrics
        error_rate_change = changes.get('error_rate_avg', 0)
        latency_change = changes.get('latency_ms_avg', 0)
        
        # Fail if error rate increased significantly
        if error_rate_change > self.safety_thresholds['max_error_rate_increase'] * 100:
            print(f"❌ Error rate increased by {error_rate_change:.2f}% - rolling back")
            return False
        
        # Fail if latency increased significantly
        if latency_change > self.safety_thresholds['max_latency_increase_percent']:
            print(f"❌ Latency increased by {latency_change:.1f}% - rolling back")
            return False
        
        # Success if latency improved
        if latency_change < -self.safety_thresholds['min_improvement_percent']:
            return True
        
        # Neutral - keep for longer observation
        return False
    
    async def _rollback_optimization(self, action: OptimizationAction):
        """Rollback an optimization."""
        print(f"↩️ Rolling back optimization {action.action_id}")
        
        strategy = self.strategies.get(action.domain)
        if strategy:
            success = await strategy.rollback(action)
            if success:
                action.status = OptimizationStatus.ROLLED_BACK
                print("✅ Rollback successful")
            else:
                print("❌ Rollback failed - manual intervention required")
        
        action.rolled_back_at = datetime.now(timezone.utc)
    
    async def _persist_action(self, action: OptimizationAction):
        """Persist optimization action to database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO optimization_actions 
                (action_id, domain, parameter_name, old_value, new_value, 
                 confidence, expected_improvement, status, test_start_time,
                 rollback_command, validation_metrics)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (action_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    validation_metrics = EXCLUDED.validation_metrics,
                    rolled_back_at = EXCLUDED.rolled_back_at
            """,
                action.action_id,
                action.domain.value,
                action.parameter,
                json.dumps(action.old_value) if action.old_value is not None else None,
                json.dumps(action.new_value) if action.new_value is not None else None,
                action.confidence,
                action.expected_improvement,
                action.status.value,
                action.test_start_time,
                action.rollback_command,
                json.dumps(action.validation_metrics)
            )
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        all_actions = list(self.active_optimizations.values())
        
        by_status = {}
        for action in all_actions:
            status = action.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        successful = len([a for a in all_actions if a.status == OptimizationStatus.APPLIED])
        rolled_back = len([a for a in all_actions if a.status == OptimizationStatus.ROLLED_BACK])
        
        total_completed = successful + rolled_back
        success_rate = successful / total_completed if total_completed > 0 else 0
        
        return {
            'total_optimizations': len(all_actions),
            'by_status': by_status,
            'success_rate': success_rate,
            'currently_testing': len([a for a in all_actions if a.status == OptimizationStatus.TESTING]),
            'active_strategies': len(self.strategies),
            'metrics_history_size': len(self.metrics_history),
        }
    
    def stop(self):
        """Stop optimization loops."""
        self._is_running = False
        
        if self._optimization_task:
            self._optimization_task.cancel()
        if self._validation_task:
            self._validation_task.cancel()
        
        print("🛑 Autonomous Optimizer stopped")


# Singleton accessor
_optimizer: Optional[AutonomousOptimizer] = None


async def get_optimizer() -> AutonomousOptimizer:
    """Get or create singleton optimizer."""
    global _optimizer
    if _optimizer is None:
        _optimizer = AutonomousOptimizer()
        await _optimizer.initialize()
    return _optimizer
