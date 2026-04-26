"""
Self-Healing Orchestrator

Detects system failures before they cascade and automatically remediates.
Implements the healing strategies from the MAL architecture.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json

import aiohttp
import asyncpg


class Severity(Enum):
    """Failure severity levels with response time requirements."""
    CRITICAL = "critical"    # < 5s response
    WARNING = "warning"      # < 60s response
    DEGRADED = "degraded"    # < 5min response
    ANOMALY = "anomaly"      # Next cycle


class HealingAction(Enum):
    """Available healing actions."""
    RESTART_SERVICE = "restart_service"
    CIRCUIT_BREAKER = "circuit_breaker"
    FAILOVER = "failover"
    CONFIG_ROLLBACK = "config_rollback"
    POOL_RESET = "pool_reset"
    CACHE_INVALIDATE = "cache_invalidate"
    SCALE_UP = "scale_up"
    ESCALATE_HUMAN = "escalate_human"


@dataclass
class Symptom:
    """A detected system symptom."""
    symptom_id: str
    service: str
    symptom_type: str  # "error_rate", "latency_spike", "connection_loss", etc.
    severity: Severity
    detected_at: datetime
    description: str
    metrics: Dict[str, Any]
    context: Dict[str, Any]


@dataclass
class Diagnosis:
    """Root cause diagnosis."""
    diagnosis_id: str
    symptom: Symptom
    root_cause: str
    confidence: float
    related_symptoms: List[str]
    suggested_actions: List[HealingAction]


@dataclass
class HealingEvent:
    """A healing action execution."""
    event_id: str
    triggered_at: datetime
    service: str
    symptom: Symptom
    diagnosis: Diagnosis
    action_taken: HealingAction
    action_params: Dict[str, Any]
    outcome: str  # "success", "failure", "partial"
    time_to_recovery_ms: int
    human_notified: bool


class HealthMonitor:
    """Monitors system health metrics."""
    
    def __init__(self, check_interval_seconds: float = 10.0):
        self.check_interval = check_interval_seconds
        self._running = False
        self._health_checks: Dict[str, Callable] = {}
        self._thresholds: Dict[str, Dict] = {}
        self._symptom_history: List[Symptom] = []
        self._on_symptom_callbacks: List[Callable] = []
    
    def register_health_check(self, service: str, check_func: Callable, 
                             thresholds: Dict[str, Any]):
        """Register a service for health monitoring."""
        self._health_checks[service] = check_func
        self._thresholds[service] = thresholds
    
    def on_symptom(self, callback: Callable):
        """Register callback for symptom detection."""
        self._on_symptom_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        self._running = True
        while self._running:
            for service, check_func in self._health_checks.items():
                try:
                    health_data = await check_func()
                    await self._evaluate_health(service, health_data)
                except Exception as e:
                    # Service is down or unresponsive
                    await self._detect_symptom(
                        service=service,
                        symptom_type="unresponsive",
                        severity=Severity.CRITICAL,
                        description=f"Health check failed: {str(e)}",
                        metrics={"error": str(e)}
                    )
            
            await asyncio.sleep(self.check_interval)
    
    async def _evaluate_health(self, service: str, health_data: Dict[str, Any]):
        """Evaluate health data against thresholds."""
        thresholds = self._thresholds.get(service, {})
        
        # Check error rate
        error_rate = health_data.get('error_rate', 0)
        if error_rate > thresholds.get('error_rate_critical', 0.1):
            await self._detect_symptom(
                service=service,
                symptom_type="error_rate_spike",
                severity=Severity.CRITICAL,
                description=f"Error rate critical: {error_rate:.2%}",
                metrics={'error_rate': error_rate, 'threshold': 0.1}
            )
        elif error_rate > thresholds.get('error_rate_warning', 0.05):
            await self._detect_symptom(
                service=service,
                symptom_type="error_rate_elevated",
                severity=Severity.WARNING,
                description=f"Error rate elevated: {error_rate:.2%}",
                metrics={'error_rate': error_rate, 'threshold': 0.05}
            )
        
        # Check latency
        latency_ms = health_data.get('avg_latency_ms', 0)
        if latency_ms > thresholds.get('latency_critical_ms', 5000):
            await self._detect_symptom(
                service=service,
                symptom_type="latency_critical",
                severity=Severity.CRITICAL,
                description=f"Latency critical: {latency_ms}ms",
                metrics={'latency_ms': latency_ms, 'threshold_ms': 5000}
            )
        elif latency_ms > thresholds.get('latency_warning_ms', 1000):
            await self._detect_symptom(
                service=service,
                symptom_type="latency_elevated",
                severity=Severity.WARNING,
                description=f"Latency elevated: {latency_ms}ms",
                metrics={'latency_ms': latency_ms, 'threshold_ms': 1000}
            )
        
        # Check resource usage
        cpu_percent = health_data.get('cpu_percent', 0)
        if cpu_percent > thresholds.get('cpu_critical', 90):
            await self._detect_symptom(
                service=service,
                symptom_type="cpu_saturation",
                severity=Severity.CRITICAL,
                description=f"CPU saturated: {cpu_percent}%",
                metrics={'cpu_percent': cpu_percent}
            )
        
        memory_percent = health_data.get('memory_percent', 0)
        if memory_percent > thresholds.get('memory_critical', 90):
            await self._detect_symptom(
                service=service,
                symptom_type="memory_pressure",
                severity=Severity.CRITICAL,
                description=f"Memory pressure: {memory_percent}%",
                metrics={'memory_percent': memory_percent}
            )
    
    async def _detect_symptom(self, service: str, symptom_type: str, 
                             severity: Severity, description: str, 
                             metrics: Dict[str, Any]):
        """Create and broadcast a symptom."""
        import uuid
        
        symptom = Symptom(
            symptom_id=str(uuid.uuid4())[:8],
            service=service,
            symptom_type=symptom_type,
            severity=severity,
            detected_at=datetime.now(timezone.utc),
            description=description,
            metrics=metrics,
            context={'recent_events': self._get_recent_symptoms(service)}
        )
        
        self._symptom_history.append(symptom)
        
        # Notify callbacks
        for callback in self._on_symptom_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(symptom)
                else:
                    callback(symptom)
            except Exception as e:
                print(f"⚠️ Symptom callback error: {e}")
    
    def _get_recent_symptoms(self, service: str, minutes: int = 5) -> List[Symptom]:
        """Get recent symptoms for context."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [
            s for s in self._symptom_history 
            if s.service == service and s.detected_at > cutoff
        ]
    
    def stop(self):
        """Stop monitoring."""
        self._running = False


class SelfHealingOrchestrator:
    """
    Orchestrates self-healing actions based on detected symptoms.
    """
    
    # Service → restart command mapping
    SERVICE_RESTART_COMMANDS = {
        'auth': 'cd integration/auth && python auth_server.py &',
        'event-bus': 'cd integration/event-bus && python event_bus.py &',
        'apex-mcp': 'cd apex/apex-mcp && npm run dev &',
        'money': 'cd Money && .venv/bin/python -m uvicorn main:app --reload &',
        'b-a-p': 'cd B-A-P && poetry run uvicorn src.main:app --reload &',
    }
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self.db_pool = db_pool
        self.health_monitor = HealthMonitor()
        self._diagnosis_rules: List[Callable] = []
        self._healing_actions: Dict[HealingAction, Callable] = {
            HealingAction.RESTART_SERVICE: self._restart_service,
            HealingAction.CIRCUIT_BREAKER: self._activate_circuit_breaker,
            HealingAction.POOL_RESET: self._reset_connection_pool,
            HealingAction.CACHE_INVALIDATE: self._invalidate_cache,
            HealingAction.ESCALATE_HUMAN: self._escalate_to_human,
        }
        self._healing_history: List[HealingEvent] = []
        
        # Register default health checks
        self._register_default_checks()
    
    async def initialize(self):
        """Initialize database and monitoring."""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                "postgresql://localhost:5435/metacognitive"
            )
        
        # Ensure schema
        await self._ensure_schema()
        
        # Subscribe to health monitor
        self.health_monitor.on_symptom(self._on_symptom_detected)
        
        print("✅ Self-Healing Orchestrator initialized")
    
    async def _ensure_schema(self):
        """Create healing event log table."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS healing_actions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    triggered_at TIMESTAMPTZ DEFAULT NOW(),
                    service VARCHAR(64),
                    symptom_type VARCHAR(64),
                    symptom_severity VARCHAR(32),
                    diagnosis VARCHAR(256),
                    action_taken VARCHAR(64),
                    action_params JSONB,
                    outcome VARCHAR(32),
                    time_to_recovery_ms INTEGER,
                    human_notified BOOLEAN DEFAULT FALSE
                );
                
                CREATE INDEX IF NOT EXISTS idx_healing_time 
                    ON healing_actions(triggered_at DESC);
                CREATE INDEX IF NOT EXISTS idx_healing_service 
                    ON healing_actions(service);
            """)
    
    def _register_default_checks(self):
        """Register health checks for all services."""
        default_thresholds = {
            'error_rate_critical': 0.1,
            'error_rate_warning': 0.05,
            'latency_critical_ms': 5000,
            'latency_warning_ms': 1000,
            'cpu_critical': 90,
            'memory_critical': 90,
        }
        
        services = ['auth', 'event-bus', 'apex-mcp', 'money', 'b-a-p']
        
        for service in services:
            self.health_monitor.register_health_check(
                service=service,
                check_func=self._make_health_check(service),
                thresholds=default_thresholds
            )
    
    def _make_health_check(self, service: str) -> Callable:
        """Create health check function for a service."""
        health_endpoints = {
            'auth': 'http://localhost:8080/health',
            'event-bus': 'http://localhost:8081/health',
            'apex-mcp': 'http://localhost:4000/health',
            'money': 'http://localhost:8000/health',
            'b-a-p': 'http://localhost:8000/health',
        }
        
        async def check():
            url = health_endpoints.get(service)
            if not url:
                return {'status': 'unknown'}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        data = await resp.json()
                        return {
                            'status': 'healthy' if resp.status == 200 else 'unhealthy',
                            'latency_ms': 0,  # Would measure actual
                            **data
                        }
            except Exception as e:
                return {
                    'status': 'unreachable',
                    'error': str(e)
                }
        
        return check
    
    async def _on_symptom_detected(self, symptom: Symptom):
        """Handle detected symptom."""
        print(f"🚨 Symptom detected: {symptom.service} - {symptom.symptom_type} ({symptom.severity.value})")
        
        # Diagnose
        diagnosis = await self._diagnose(symptom)
        
        # Determine if auto-healing is appropriate
        if symptom.severity == Severity.CRITICAL:
            # Auto-heal immediately
            await self._execute_healing(diagnosis, auto_execute=True)
        elif symptom.severity == Severity.WARNING:
            # Prepare healing, notify ops
            await self._execute_healing(diagnosis, auto_execute=False)
        else:
            # Log for analysis
            await self._log_diagnosis(diagnosis)
    
    async def _diagnose(self, symptom: Symptom) -> Diagnosis:
        """Diagnose root cause from symptom."""
        import uuid
        
        # Simple rule-based diagnosis
        root_cause = "unknown"
        confidence = 0.5
        suggested_actions = []
        
        if symptom.symptom_type == "unresponsive":
            root_cause = "service_crash_or_hang"
            confidence = 0.9
            suggested_actions = [HealingAction.RESTART_SERVICE]
        
        elif symptom.symptom_type == "error_rate_spike":
            root_cause = "downstream_dependency_failure"
            confidence = 0.7
            suggested_actions = [HealingAction.CIRCUIT_BREAKER, HealingAction.ESCALATE_HUMAN]
        
        elif symptom.symptom_type == "latency_critical":
            root_cause = "resource_saturation_or_db_slowdown"
            confidence = 0.6
            suggested_actions = [HealingAction.POOL_RESET, HealingAction.SCALE_UP]
        
        elif symptom.symptom_type == "memory_pressure":
            root_cause = "memory_leak_or_insufficient_capacity"
            confidence = 0.75
            suggested_actions = [HealingAction.RESTART_SERVICE]
        
        elif symptom.symptom_type == "cpu_saturation":
            root_cause = "compute_intensive_workload_or_infinite_loop"
            confidence = 0.65
            suggested_actions = [HealingAction.ESCALATE_HUMAN]
        
        return Diagnosis(
            diagnosis_id=str(uuid.uuid4())[:8],
            symptom=symptom,
            root_cause=root_cause,
            confidence=confidence,
            related_symptoms=[s.symptom_id for s in symptom.context.get('recent_events', [])],
            suggested_actions=suggested_actions
        )
    
    async def _execute_healing(self, diagnosis: Diagnosis, auto_execute: bool):
        """Execute healing actions."""
        for action in diagnosis.suggested_actions:
            if action not in self._healing_actions:
                continue
            
            if not auto_execute and action != HealingAction.ESCALATE_HUMAN:
                # Prepare but don't execute yet
                print(f"⏸️  Prepared {action.value} for {diagnosis.symptom.service}")
                continue
            
            # Execute healing
            start_time = datetime.now(timezone.utc)
            print(f"🔧 Executing {action.value} on {diagnosis.symptom.service}...")
            
            try:
                result = await self._healing_actions[action](diagnosis.symptom.service)
                outcome = "success" if result else "partial"
            except Exception as e:
                print(f"❌ Healing action failed: {e}")
                outcome = "failure"
            
            # Calculate recovery time
            recovery_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            # Log healing event
            event = HealingEvent(
                event_id=str(__import__('uuid').uuid4())[:8],
                triggered_at=start_time,
                service=diagnosis.symptom.service,
                symptom=diagnosis.symptom,
                diagnosis=diagnosis,
                action_taken=action,
                action_params={},
                outcome=outcome,
                time_to_recovery_ms=recovery_ms,
                human_notified=not auto_execute
            )
            
            self._healing_history.append(event)
            await self._persist_healing_event(event)
            
            print(f"✅ Healing complete: {outcome} ({recovery_ms}ms)")
    
    async def _persist_healing_event(self, event: HealingEvent):
        """Persist healing event to database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO healing_actions 
                (service, symptom_type, symptom_severity, diagnosis, action_taken,
                 action_params, outcome, time_to_recovery_ms, human_notified)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                event.service,
                event.symptom.symptom_type,
                event.symptom.severity.value,
                event.diagnosis.root_cause,
                event.action_taken.value,
                json.dumps(event.action_params),
                event.outcome,
                event.time_to_recovery_ms,
                event.human_notified
            )
    
    # Healing action implementations
    
    async def _restart_service(self, service: str) -> bool:
        """Restart a service using safe subprocess execution."""
        if not service or not isinstance(service, str):
            print(f"⚠️ Invalid service name: {service}")
            return False

        # Sanitize service name to prevent injection
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', service):
            print(f"⚠️ Invalid service name format: {service}")
            return False

        try:
            # Use exec instead of shell for security (prevents shell injection)
            proc = await asyncio.create_subprocess_exec(
                "docker", "compose", "restart", service,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait_for(proc.wait(), timeout=30.0)
            
            # Wait for health check to pass
            for attempt in range(10):
                await asyncio.sleep(2)
                check = await self._make_health_check(service)()
                if check.get('status') == 'healthy':
                    return True
            
            return False
        except Exception as e:
            print(f"❌ Restart failed: {e}")
            return False
    
    async def _activate_circuit_breaker(self, service: str) -> bool:
        """Activate circuit breaker for a service."""
        # Would integrate with Kong or internal circuit breaker
        print(f"🔌 Circuit breaker activated for {service}")
        return True
    
    async def _reset_connection_pool(self, service: str) -> bool:
        """Reset database connection pool."""
        # Would send signal to service to reset pools
        print(f"🔄 Connection pool reset for {service}")
        return True
    
    async def _invalidate_cache(self, service: str) -> bool:
        """Invalidate service cache."""
        # Would send cache invalidation to Redis
        print(f"🗑️  Cache invalidated for {service}")
        return True
    
    async def _escalate_to_human(self, service: str) -> bool:
        """Escalate to human operator."""
        # Would send alert via PagerDuty, Slack, etc.
        print(f"📟 Escalated {service} to human operators")
        return True
    
    async def _log_diagnosis(self, diagnosis: Diagnosis):
        """Log diagnosis without action."""
        print(f"📝 Logged: {diagnosis.root_cause} ({diagnosis.confidence:.0%} confidence)")
    
    async def start(self):
        """Start healing orchestration."""
        await self.health_monitor.start_monitoring()
    
    def stop(self):
        """Stop healing orchestration."""
        self.health_monitor.stop()
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """Get healing statistics."""
        if not self._healing_history:
            return {'healing_events': 0, 'success_rate': 0}
        
        recent = [e for e in self._healing_history 
                 if e.triggered_at > datetime.now(timezone.utc) - timedelta(hours=24)]
        
        successes = sum(1 for e in recent if e.outcome == "success")
        
        return {
            'healing_events_24h': len(recent),
            'success_rate': successes / len(recent) if recent else 0,
            'avg_recovery_time_ms': sum(e.time_to_recovery_ms for e in recent) / len(recent) if recent else 0,
            'services_healed': list(set(e.service for e in recent)),
        }


# Singleton instance
_orchestrator: Optional[SelfHealingOrchestrator] = None


async def get_orchestrator() -> SelfHealingOrchestrator:
    """Get or create singleton orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SelfHealingOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator
