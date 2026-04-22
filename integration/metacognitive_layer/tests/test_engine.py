"""
Tests for MetacognitiveEngine - Core pattern recognition and prediction.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from ..engine import (
    Pattern, Observation, Prediction, 
    CognitiveBudget
)


@pytest.mark.asyncio
async def test_observation_creation(engine):
    """Test that observations are created correctly."""
    event_data = {
        'service': 'test_service',
        'operation': 'test_operation',
        'duration_ms': 100,
        'status': 'success',
        'metadata': {'key': 'value'}
    }
    
    obs = Observation(
        observation_id='test_id',
        timestamp=datetime.now(timezone.utc),
        service=event_data['service'],
        operation=event_data['operation'],
        duration_ms=event_data['duration_ms'],
        status=event_data['status'],
        metadata=event_data['metadata'],
        context_hash=''
    )
    
    obs.context_hash = obs.compute_signature()
    
    assert obs.service == 'test_service'
    assert obs.operation == 'test_operation'
    assert obs.context_hash is not None
    assert len(obs.context_hash) == 32


@pytest.mark.asyncio
async def test_pattern_confidence_update(engine):
    """Test Bayesian confidence update for patterns."""
    pattern = Pattern(
        pattern_id='test_pattern',
        pattern_type='test',
        signature='abc123',
        context_features={'service': 'test'},
        success_rate=0.5,
        avg_duration_ms=100,
        occurrence_count=10,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        confidence_score=0.5
    )
    
    # Update with success
    pattern.update_confidence(new_success=True, duration_ms=90)
    
    assert pattern.occurrence_count == 11
    assert pattern.success_rate > 0.5  # Should increase
    assert pattern.avg_duration_ms < 100  # Should average down
    assert pattern.confidence_score > 0.5


@pytest.mark.asyncio
async def test_cognitive_budget_allocation(engine):
    """Test cognitive budget prioritization."""
    budget = CognitiveBudget(max_concurrent_analyses=2, analysis_time_budget_ms=500)
    
    # High priority observation (error)
    error_obs = Observation(
        observation_id='1',
        timestamp=datetime.now(timezone.utc),
        service='test',
        operation='op',
        duration_ms=0,
        status='error',
        metadata={},
        context_hash='hash1'
    )
    
    allocated = await budget.allocate_attention(error_obs)
    assert allocated is True
    
    # Low priority observation (success, fast)
    success_obs = Observation(
        observation_id='2',
        timestamp=datetime.now(timezone.utc),
        service='test',
        operation='op',
        duration_ms=50,
        status='success',
        metadata={},
        context_hash='hash2'
    )
    
    # Should still allocate (within limits)
    allocated = await budget.allocate_attention(success_obs)
    assert allocated is True


@pytest.mark.asyncio
async def test_prediction_actionability(engine):
    """Test that predictions correctly determine actionability."""
    # Critical confidence prediction
    pred_critical = Prediction(
        prediction_id='1',
        predicted_at=datetime.now(timezone.utc),
        prediction_type='test',
        confidence=0.96,
        predicted_action={'action': 'test'},
        trigger_features={}
    )
    
    assert pred_critical.is_actionable() is True
    
    # Low confidence prediction
    pred_low = Prediction(
        prediction_id='2',
        predicted_at=datetime.now(timezone.utc),
        prediction_type='test',
        confidence=0.4,
        predicted_action={'action': 'test'},
        trigger_features={}
    )
    
    assert pred_low.is_actionable() is False


@pytest.mark.asyncio
async def test_engine_initialization(engine, mock_db_pool):
    """Test engine initialization with database."""
    # Mock the database operations
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    engine.db_pool = mock_db_pool
    
    engine.db_pool = mock_db_pool
    
    await engine.initialize()
    
    # Should have created tables
    assert mock_conn.execute.called


@pytest.mark.asyncio
async def test_engine_observe_buffers_events(engine):
    """Test that observations are buffered for batch processing."""
    event_data = {
        'service': 'test',
        'operation': 'op',
        'duration_ms': 100,
        'status': 'success',
        'metadata': {}
    }
    
    engine.db_pool = None  # Don't try to persist
    await engine.observe(event_data)
    
    assert len(engine.observation_buffer) == 1


@pytest.mark.asyncio
async def test_pattern_inference(engine):
    """Test pattern type inference from observations."""
    error_obs = Observation(
        observation_id='1',
        timestamp=datetime.now(timezone.utc),
        service='test',
        operation='op',
        duration_ms=0,
        status='error',
        metadata={},
        context_hash='hash1'
    )
    
    pattern_type = engine._infer_pattern_type(error_obs)
    assert pattern_type == 'error_pattern'
    
    slow_obs = Observation(
        observation_id='2',
        timestamp=datetime.now(timezone.utc),
        service='test',
        operation='op',
        duration_ms=2000,
        status='success',
        metadata={},
        context_hash='hash2'
    )
    
    pattern_type = engine._infer_pattern_type(slow_obs)
    assert pattern_type == 'slow_operation'


@pytest.mark.asyncio
async def test_engine_insights(engine):
    """Test getting insights from the engine."""
    engine.db_pool = None
    
    insights = engine.get_insights()
    
    assert 'status' in insights
    assert 'patterns_learned' in insights
    assert 'active_predictions' in insights
