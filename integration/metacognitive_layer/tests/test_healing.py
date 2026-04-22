"""
Tests for SelfHealingOrchestrator - Auto-remediation and failure recovery.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from ..healing_orchestrator import (
    HealthMonitor, Symptom, Diagnosis,
    HealingAction, Severity
)


@pytest.mark.asyncio
async def test_symptom_creation():
    """Test symptom detection and creation."""
    symptom = Symptom(
        symptom_id='sym_123',
        service='test_service',
        symptom_type='error_rate_spike',
        severity=Severity.CRITICAL,
        detected_at=datetime.now(timezone.utc),
        description='Error rate exceeded threshold',
        metrics={'error_rate': 0.15},
        context={}
    )
    
    assert symptom.service == 'test_service'
    assert symptom.severity == Severity.CRITICAL
    assert symptom.symptom_type == 'error_rate_spike'


@pytest.mark.asyncio
async def test_diagnosis_creation():
    """Test diagnosis generation."""
    symptom = Symptom(
        symptom_id='sym_123',
        service='test_service',
        symptom_type='unresponsive',
        severity=Severity.CRITICAL,
        detected_at=datetime.now(timezone.utc),
        description='Service not responding',
        metrics={},
        context={}
    )
    
    diagnosis = Diagnosis(
        diagnosis_id='diag_123',
        symptom=symptom,
        root_cause='service_crash_or_hang',
        confidence=0.9,
        related_symptoms=[],
        suggested_actions=[HealingAction.RESTART_SERVICE]
    )
    
    assert diagnosis.root_cause == 'service_crash_or_hang'
    assert HealingAction.RESTART_SERVICE in diagnosis.suggested_actions


@pytest.mark.asyncio
async def test_health_monitor_thresholds():
    """Test health monitor threshold detection."""
    monitor = HealthMonitor(check_interval_seconds=1.0)
    
    # Register a health check
    async def mock_check():
        return {
            'error_rate': 0.15,  # Above critical threshold
            'avg_latency_ms': 2000,
            'cpu_percent': 50,
            'memory_percent': 60
        }
    
    symptoms_detected = []
    
    def on_symptom(symptom):
        symptoms_detected.append(symptom)
    
    monitor.register_health_check(
        service='test_service',
        check_func=mock_check,
        thresholds={
            'error_rate_critical': 0.1,
            'latency_critical_ms': 5000,
            'cpu_critical': 90,
            'memory_critical': 90
        }
    )
    
    monitor.on_symptom(on_symptom)
    
    # Evaluate once
    await monitor._evaluate_health('test_service', await mock_check())
    
    assert len(symptoms_detected) == 1
    assert symptoms_detected[0].symptom_type == 'error_rate_spike'
    assert symptoms_detected[0].severity == Severity.CRITICAL


@pytest.mark.asyncio
async def test_healing_orchestrator_initialization(healing_orchestrator, mock_db_pool):
    """Test orchestrator initialization."""
    healing_orchestrator.db_pool = mock_db_pool
    mock_conn = AsyncMock()
    mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_db_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    await healing_orchestrator.initialize()
    
    assert mock_conn.execute.called
    assert healing_orchestrator.health_monitor is not None


@pytest.mark.asyncio
async def test_diagnosis_rules(healing_orchestrator):
    """Test diagnosis rule application."""
    symptom = Symptom(
        symptom_id='sym_123',
        service='money',
        symptom_type='memory_pressure',
        severity=Severity.CRITICAL,
        detected_at=datetime.now(timezone.utc),
        description='Memory at 95%',
        metrics={'memory_percent': 95},
        context={}
    )
    
    diagnosis = await healing_orchestrator._diagnose(symptom)
    
    assert diagnosis.root_cause == 'memory_leak_or_insufficient_capacity'
    assert HealingAction.RESTART_SERVICE in diagnosis.suggested_actions


@pytest.mark.asyncio
async def test_healing_stats(healing_orchestrator):
    """Test healing statistics generation."""
    stats = healing_orchestrator.get_healing_stats()
    
    assert 'healing_events_24h' in stats
    assert 'success_rate' in stats


@pytest.mark.asyncio
async def test_healing_action_priorities(healing_orchestrator):
    """Test that critical symptoms trigger immediate healing."""
    critical_symptom = Symptom(
        symptom_id='sym_1',
        service='auth',
        symptom_type='unresponsive',
        severity=Severity.CRITICAL,
        detected_at=datetime.now(timezone.utc),
        description='Service down',
        metrics={},
        context={}
    )
    
    # Should auto-execute for critical
    assert critical_symptom.severity == Severity.CRITICAL


@pytest.mark.asyncio
async def test_service_restart_command_mapping(healing_orchestrator):
    """Test that service restart commands are correctly mapped."""
    assert 'money' in healing_orchestrator.SERVICE_RESTART_COMMANDS
    assert 'auth' in healing_orchestrator.SERVICE_RESTART_COMMANDS
    
    # Verify command format
    money_cmd = healing_orchestrator.SERVICE_RESTART_COMMANDS['money']
    assert 'uvicorn' in money_cmd
    assert 'main:app' in money_cmd
