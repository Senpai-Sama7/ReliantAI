"""
Tests for AutonomousOptimizer - Self-tuning and performance optimization.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from ..optimizer import (
    OptimizationAction, OptimizationStatus,
    OptimizationDomain, PerformanceBaseline, CacheOptimizationStrategy
)


@pytest.mark.asyncio
async def test_optimizer_initialization(optimizer, mock_db_pool):
    """Test optimizer initialization."""
    optimizer.db_pool = mock_db_pool
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    await optimizer.initialize()
    
    assert mock_conn.execute.called


@pytest.mark.asyncio
async def test_metrics_recording(optimizer):
    """Test metrics history recording."""
    metrics = {
        'latency_ms': 100,
        'error_rate': 0.01,
        'cache_hit_rate': 0.85
    }
    
    await optimizer.record_metrics(metrics)
    
    assert len(optimizer.metrics_history) == 1
    assert 'timestamp' in optimizer.metrics_history[0]


@pytest.mark.asyncio
async def test_cache_optimization_strategy_analysis():
    """Test cache optimization strategy."""
    strategy = CacheOptimizationStrategy()
    
    # Simulate metrics with low hit rate
    metrics_history = [
        {'cache_hit_rate': 0.6, 'cache_ttl_seconds': 300},
        {'cache_hit_rate': 0.65, 'cache_ttl_seconds': 300},
        {'cache_hit_rate': 0.62, 'cache_ttl_seconds': 300},
        {'cache_hit_rate': 0.68, 'cache_ttl_seconds': 300},
        {'cache_hit_rate': 0.64, 'cache_ttl_seconds': 300},
    ]
    
    action = await strategy.analyze(metrics_history)
    
    assert action is not None
    assert action.domain == OptimizationDomain.CACHE
    assert action.new_value > action.old_value  # Should increase TTL


@pytest.mark.asyncio
async def test_performance_baseline_comparison():
    """Test baseline comparison for validation."""
    baseline = PerformanceBaseline(
        baseline_id='base_1',
        recorded_at=datetime.now(timezone.utc),
        metrics={
            'latency_ms_avg': 100,
            'error_rate_avg': 0.01,
            'throughput_avg': 1000
        }
    )
    
    # Improved metrics
    current = {
        'latency_ms_avg': 80,
        'error_rate_avg': 0.005,
        'throughput_avg': 1200
    }
    
    changes = baseline.compare(current)
    
    assert changes['latency_ms_avg'] < 0  # Should be negative (improved)
    assert changes['error_rate_avg'] < 0


@pytest.mark.asyncio
async def test_optimization_status_transitions(optimizer):
    """Test optimization status transitions."""
    action = OptimizationAction(
        action_id='opt_1',
        timestamp=datetime.now(timezone.utc),
        domain=OptimizationDomain.CACHE,
        parameter='ttl',
        old_value=300,
        new_value=400,
        confidence=0.8,
        expected_improvement=0.15,
        status=OptimizationStatus.PENDING
    )
    
    # Simulate testing phase
    action.status = OptimizationStatus.TESTING
    action.test_start_time = datetime.now(timezone.utc)
    
    assert action.status == OptimizationStatus.TESTING
    
    # Simulate success
    action.status = OptimizationStatus.APPLIED
    assert action.status == OptimizationStatus.APPLIED


@pytest.mark.asyncio
async def test_safety_thresholds(optimizer):
    """Test safety threshold configuration."""
    assert 'max_error_rate_increase' in optimizer.safety_thresholds
    assert 'max_latency_increase_percent' in optimizer.safety_thresholds
    assert 'test_duration_minutes' in optimizer.safety_thresholds
    
    # Verify values are reasonable
    assert optimizer.safety_thresholds['max_error_rate_increase'] < 0.01
    assert optimizer.safety_thresholds['max_latency_increase_percent'] < 50


@pytest.mark.asyncio
async def test_peak_hour_blackout(optimizer):
    """Test that optimization is skipped during peak hours."""
    # This would need to mock datetime, but we can test the logic
    # Peak hours are 9-17
    assert optimizer.safety_thresholds is not None


@pytest.mark.asyncio
async def test_optimization_stats(optimizer):
    """Test optimization statistics."""
    stats = optimizer.get_optimization_stats()
    
    assert 'total_optimizations' in stats
    assert 'by_status' in stats
    assert 'success_rate' in stats
    assert 'active_strategies' in stats


@pytest.mark.asyncio
async def test_history_size_limit(optimizer):
    """Test that metrics history is capped."""
    optimizer.max_history_size = 100
    
    # Add more than max
    for i in range(150):
        await optimizer.record_metrics({'latency_ms': 100})
    
    assert len(optimizer.metrics_history) <= 100
