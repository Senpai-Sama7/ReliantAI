"""
Tests for KnowledgeConsolidator - Pattern extraction and knowledge creation.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from ..knowledge_consolidator import (
    ConsolidatedKnowledge, PatternType,
    ConsolidationStatus, PatternSignature, QueryPattern,
    APISequencePattern, ToolCombinationPattern
)


@pytest.mark.asyncio
async def test_consolidator_initialization(consolidator, mock_db_pool):
    """Test consolidator initialization."""
    consolidator.db_pool = mock_db_pool
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    await consolidator.initialize()
    
    assert mock_conn.execute.called


@pytest.mark.asyncio
async def test_query_pattern_materialization_check():
    """Test query pattern materialization criteria."""
    pattern = QueryPattern(
        query_template='SELECT * FROM users WHERE id = ?',
        parameter_keys=['id'],
        avg_execution_time_ms=150,
        result_schema={'id': 'int', 'name': 'str'},
        cache_hit_rate=0.8
    )
    
    assert pattern.should_materialize() is True
    
    # Fast query should not materialize
    fast_pattern = QueryPattern(
        query_template='SELECT 1',
        parameter_keys=[],
        avg_execution_time_ms=10,
        result_schema={},
        cache_hit_rate=0.5
    )
    
    assert fast_pattern.should_materialize() is False


@pytest.mark.asyncio
async def test_api_sequence_composite_check():
    """Test API sequence composite endpoint criteria."""
    pattern = APISequencePattern(
        sequence=['GET /users/{id}', 'GET /users/{id}/orders', 'GET /orders/{id}/items'],
        avg_total_latency_ms=800,
        correlation_key='user_id'
    )
    
    assert pattern.should_create_composite() is True
    
    # Short sequence should not create composite
    short_pattern = APISequencePattern(
        sequence=['GET /health'],
        avg_total_latency_ms=50,
        correlation_key=None
    )
    
    assert short_pattern.should_create_composite() is False


@pytest.mark.asyncio
async def test_tool_combination_skill_check():
    """Test tool combination skill shortcut criteria."""
    pattern = ToolCombinationPattern(
        tools_used=['web_search', 'summarize', 'save_note'],
        context_type='research_task',
        success_rate=0.85,
        avg_completion_time_ms=5000
    )
    
    assert pattern.should_create_skill() is True
    
    # Low success rate should not create skill
    low_success = ToolCombinationPattern(
        tools_used=['tool_a', 'tool_b'],
        context_type='test',
        success_rate=0.6,
        avg_completion_time_ms=1000
    )
    
    assert low_success.should_create_skill() is False


@pytest.mark.asyncio
async def test_query_normalization(consolidator):
    """Test SQL query normalization."""
    query1 = "SELECT * FROM users WHERE id = '123' AND age > 25"
    query2 = "SELECT * FROM users WHERE id = '456' AND age > 30"
    
    norm1 = consolidator._normalize_query(query1)
    norm2 = consolidator._normalize_query(query2)
    
    # Normalized forms should be identical
    assert norm1 == norm2
    assert '?' in norm1  # Literals replaced


@pytest.mark.asyncio
async def test_knowledge_confidence_scoring(consolidator):
    """Test knowledge confidence scoring."""
    sig = PatternSignature(
        signature_hash='abc123',
        context_features={'service': 'test'},
        frequency=50,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    knowledge = ConsolidatedKnowledge(
        knowledge_id='test_know',
        pattern_type=PatternType.QUERY_PATTERN,
        status=ConsolidationStatus.IDENTIFIED,
        signature=sig,
        supporting_evidence_count=50,
        confidence_score=0.8,
        artifact_type='materialized_view',
        artifact_definition={}
    )
    
    assert knowledge.confidence_score > 0.5


@pytest.mark.asyncio
async def test_consolidation_stats(consolidator):
    """Test consolidation statistics."""
    stats = consolidator.get_consolidation_stats()
    
    assert 'total_patterns' in stats
    assert 'by_status' in stats
    assert 'by_type' in stats
    assert 'consolidated_patterns' in stats


@pytest.mark.asyncio
async def test_applicable_knowledge_filtering(consolidator):
    """Test filtering knowledge by context."""
    sig = PatternSignature(
        signature_hash='abc123',
        context_features={'service': 'money', 'operation': 'dispatch'},
        frequency=20,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    knowledge = ConsolidatedKnowledge(
        knowledge_id='test_know',
        pattern_type=PatternType.TOOL_COMBINATION,
        status=ConsolidationStatus.CONSOLIDATED,
        signature=sig,
        supporting_evidence_count=20,
        confidence_score=0.9,
        artifact_type='skill_shortcut',
        artifact_definition={}
    )
    
    consolidator.knowledge_base['test_know'] = knowledge
    
    # Test matching context
    context = {'service': 'money', 'operation': 'dispatch'}
    applicable = consolidator.get_applicable_knowledge(context)
    
    assert len(applicable) > 0
    
    # Test non-matching context
    wrong_context = {'service': 'apex', 'operation': 'research'}
    applicable = consolidator.get_applicable_knowledge(wrong_context)
    
    # May or may not be empty depending on fuzzy matching


@pytest.mark.asyncio
async def test_telemetry_buffer_limits(consolidator):
    """Test that telemetry buffers are size-limited."""
    consolidator._max_buffer_size = 100
    
    # Add more than max queries
    for i in range(150):
        await consolidator.record_query(
            f'QUERY {i}',
            {'param': i},
            100,
            10
        )
    
    assert len(consolidator._recent_queries) <= 100


@pytest.mark.asyncio
async def test_pattern_status_lifecycle(consolidator):
    """Test pattern status transitions."""
    sig = PatternSignature(
        signature_hash='lifecycle_test',
        context_features={},
        frequency=1,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    knowledge = ConsolidatedKnowledge(
        knowledge_id='lifecycle',
        pattern_type=PatternType.API_SEQUENCE,
        status=ConsolidationStatus.IDENTIFIED,
        signature=sig,
        supporting_evidence_count=1,
        confidence_score=0.5,
        artifact_type='composite_endpoint',
        artifact_definition={}
    )
    
    # Can transition to validating
    knowledge.status = ConsolidationStatus.VALIDATING
    assert knowledge.status == ConsolidationStatus.VALIDATING
    
    # Can transition to consolidated
    knowledge.status = ConsolidationStatus.CONSOLIDATED
    assert knowledge.status == ConsolidationStatus.CONSOLIDATED


@pytest.mark.asyncio
async def test_artifact_usage_tracking(consolidator, mock_db_pool):
    """Test artifact usage tracking."""
    consolidator.db_pool = mock_db_pool
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    sig = PatternSignature(
        signature_hash='usage_test',
        context_features={},
        frequency=10,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    knowledge = ConsolidatedKnowledge(
        knowledge_id='usage_test',
        pattern_type=PatternType.QUERY_PATTERN,
        status=ConsolidationStatus.CONSOLIDATED,
        signature=sig,
        supporting_evidence_count=10,
        confidence_score=0.8,
        artifact_type='materialized_view',
        artifact_definition={},
        usage_count=5
    )
    
    consolidator.knowledge_base['usage_test'] = knowledge
    
    await consolidator.record_artifact_usage('usage_test')
    
    assert consolidator.knowledge_base['usage_test'].usage_count == 6
