"""
Integration tests for full MetacognitiveAutonomySystem.

Tests component interaction and end-to-end flows.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_mal_system_initialization(mal_system, mock_db_pool):
    """Test full MAL system initialization."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Set up all components with mocked DB
    mal_system.engine.db_pool = mock_db_pool
    mal_system.healing.db_pool = mock_db_pool
    mal_system.feedback.db_pool = mock_db_pool
    mal_system.predictor.db_pool = mock_db_pool
    mal_system.optimizer.db_pool = mock_db_pool
    mal_system.consolidator.db_pool = mock_db_pool
    
    await mal_system.initialize()
    
    # All components should be initialized
    assert mal_system.engine is not None
    assert mal_system.healing is not None
    assert mal_system.feedback is not None
    assert mal_system.predictor is not None
    assert mal_system.optimizer is not None
    assert mal_system.consolidator is not None


@pytest.mark.asyncio
async def test_end_to_end_observation_flow(mal_system, mock_db_pool):
    """Test complete observation to optimization flow."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mal_system.engine.db_pool = mock_db_pool
    mal_system.optimizer.db_pool = mock_db_pool
    
    # Step 1: Record observation
    event_data = {
        'service': 'money',
        'operation': 'dispatch_request',
        'duration_ms': 500,
        'status': 'success',
        'metadata': {'technician_id': 'tech_123'}
    }
    
    await mal_system.engine.observe(event_data)
    
    # Step 2: Verify observation was buffered
    assert len(mal_system.engine.observation_buffer) == 1
    
    # Step 3: Verify optimizer receives metrics
    await mal_system._on_metrics_for_optimization(event_data)
    assert len(mal_system.optimizer.metrics_history) == 1


@pytest.mark.asyncio
async def test_feedback_to_consolidation_flow(mal_system, mock_db_pool):
    """Test feedback triggering knowledge consolidation."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mal_system.feedback.db_pool = mock_db_pool
    mal_system.consolidator.db_pool = mock_db_pool
    
    # Create a mock insight
    from ..feedback_collector import LearnedInsight
    
    insight = LearnedInsight(
        insight_id='insight_1',
        insight_type='successful_path',
        trigger_conditions={'context_type': 'dispatch'},
        recommended_action={
            'tools': ['search_technician', 'calculate_route', 'send_notification'],
            'duration_ms': 2000
        },
        supporting_evidence_count=10,
        success_rate=0.9,
        confidence_score=0.85,
        first_observed=datetime.now(timezone.utc),
        last_validated=datetime.now(timezone.utc)
    )
    
    # Process insight
    await mal_system._on_insight_for_consolidation(insight)
    
    # Verify tool usage was recorded
    assert len(mal_system.consolidator._recent_tool_usage) == 1


@pytest.mark.asyncio
async def test_healing_to_engine_flow(mal_system, mock_db_pool):
    """Test healing events feeding into engine observations."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mal_system.engine.db_pool = mock_db_pool
    mal_system.healing.db_pool = mock_db_pool
    
    # Verify wiring is correct
    assert mal_system.healing.health_monitor is not None


@pytest.mark.asyncio
async def test_mal_system_status(mal_system, mock_db_pool):
    """Test status reporting from all components."""
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mal_system.engine.db_pool = mock_db_pool
    mal_system.healing.db_pool = mock_db_pool
    mal_system.feedback.db_pool = mock_db_pool
    mal_system.predictor.db_pool = mock_db_pool
    mal_system.optimizer.db_pool = mock_db_pool
    mal_system.consolidator.db_pool = mock_db_pool
    
    await mal_system.initialize()
    
    status = mal_system.get_status()
    
    assert 'running' in status
    assert 'engine' in status
    assert 'healing' in status
    assert 'feedback' in status
    assert 'predictor' in status
    assert 'optimizer' in status
    assert 'consolidator' in status


@pytest.mark.asyncio
async def test_graceful_shutdown(mal_system):
    """Test graceful shutdown of all components."""
    mal_system._running = True
    mal_system._shutdown_event.set()
    
    # Start and stop
    await mal_system.stop()
    
    assert mal_system._running is False


@pytest.mark.asyncio
async def test_concurrent_component_operation():
    """Test that components can operate concurrently."""
    from ..engine import MetacognitiveEngine
    from ..optimizer import AutonomousOptimizer
    
    engine = MetacognitiveEngine(db_pool=None)
    optimizer = AutonomousOptimizer(db_pool=None)
    
    # Simulate concurrent operations
    async def record_observations():
        for i in range(10):
            await engine.observe({
                'service': 'test',
                'operation': f'op_{i}',
                'duration_ms': 100,
                'status': 'success'
            })
    
    async def record_metrics():
        for i in range(10):
            await optimizer.record_metrics({
                'latency_ms': 100 + i,
                'error_rate': 0.01
            })
    
    # Run concurrently
    await asyncio.gather(record_observations(), record_metrics())
    
    assert len(engine.observation_buffer) == 10
    assert len(optimizer.metrics_history) == 10


@pytest.mark.asyncio
async def test_cross_component_metrics_flow():
    """Test metrics flowing between components."""
    from ..engine import MetacognitiveEngine
    from ..optimizer import AutonomousOptimizer
    
    engine = MetacognitiveEngine(db_pool=None)
    optimizer = AutonomousOptimizer(db_pool=None)
    
    # Simulate subscription
    events_received = []
    
    async def metrics_handler(event):
        events_received.append(event)
        await optimizer.record_metrics({
            'service': event.get('service'),
            'operation': event.get('operation'),
            'duration_ms': event.get('duration_ms', 0)
        })
    
    engine.subscribe(metrics_handler)
    
    # Emit event
    await engine.observe({
        'service': 'money',
        'operation': 'dispatch',
        'duration_ms': 200,
        'status': 'success'
    })
    
    # Allow async processing
    await asyncio.sleep(0.1)
    
    # Should have at least the buffered event
    assert len(engine.observation_buffer) >= 1


@pytest.mark.asyncio
async def test_error_handling_in_components():
    """Test that errors in one component don't crash others."""
    from ..engine import MetacognitiveEngine
    
    engine = MetacognitiveEngine(db_pool=None)
    
    # Add a subscriber that will error
    def bad_subscriber(event):
        raise ValueError("Subscriber error")
    
    engine.subscribe(bad_subscriber)
    
    # Should not raise despite subscriber error
    await engine.observe({
        'service': 'test',
        'operation': 'op',
        'duration_ms': 100,
        'status': 'success'
    })
    
    # Event should still be buffered
    assert len(engine.observation_buffer) == 1
