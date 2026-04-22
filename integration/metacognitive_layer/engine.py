"""
Metacognitive Engine - Layer 5 of APEX

The "brain" that observes all system operations, recognizes patterns,
makes predictions, and drives autonomous decisions.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import statistics

import asyncpg


class ConfidenceLevel(Enum):
    """Confidence thresholds for autonomy decisions."""
    CRITICAL = 0.95  # Execute autonomously
    HIGH = 0.85      # Execute with notification
    MEDIUM = 0.70    # Prepare, ask for confirmation
    LOW = 0.50       # Log only, observe
    INSUFFICIENT = 0.0  # Need more data


@dataclass
class Pattern:
    """A learned pattern from system observations."""
    pattern_id: str
    pattern_type: str  # "api_sequence", "error_recovery", "resource_spike", etc.
    signature: str  # Hash of pattern characteristics
    context_features: Dict[str, Any]
    success_rate: float
    avg_duration_ms: float
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    confidence_score: float
    
    def update_confidence(self, new_success: bool, duration_ms: float):
        """Bayesian update of confidence score."""
        self.occurrence_count += 1
        self.last_seen = datetime.now(timezone.utc)
        
        # Update success rate with exponential smoothing
        alpha = 0.3  # Learning rate
        success_val = 1.0 if new_success else 0.0
        self.success_rate = (1 - alpha) * self.success_rate + alpha * success_val
        
        # Update duration with moving average
        self.avg_duration_ms = (
            (self.avg_duration_ms * (self.occurrence_count - 1) + duration_ms)
            / self.occurrence_count
        )
        
        # Confidence = success_rate * log(occurrence_count)
        import math
        self.confidence_score = self.success_rate * min(
            1.0, math.log10(self.occurrence_count) / 3.0
        )


@dataclass
class Observation:
    """A single system observation event."""
    observation_id: str
    timestamp: datetime
    service: str
    operation: str
    duration_ms: float
    status: str
    metadata: Dict[str, Any]
    context_hash: str
    
    def compute_signature(self) -> str:
        """Compute pattern signature from context."""
        sig_data = {
            "service": self.service,
            "operation": self.operation,
            "status": self.status,
            "hour_of_day": self.timestamp.hour,
            "day_of_week": self.timestamp.weekday(),
        }
        sig_str = json.dumps(sig_data, sort_keys=True)
        return hashlib.sha256(sig_str.encode()).hexdigest()[:32]


@dataclass
class Prediction:
    """A prediction about future system state or user intent."""
    prediction_id: str
    predicted_at: datetime
    prediction_type: str  # "intent", "failure", "load_spike", "optimal_route"
    confidence: float
    predicted_action: Dict[str, Any]
    trigger_features: Dict[str, Any]
    
    def is_actionable(self) -> bool:
        """Determine if prediction meets threshold for autonomous action."""
        if self.confidence >= ConfidenceLevel.CRITICAL.value:
            return True
        elif self.confidence >= ConfidenceLevel.HIGH.value:
            return True  # But notify
        elif self.confidence >= ConfidenceLevel.MEDIUM.value:
            return False  # Prepare only
        return False


class CognitiveBudget:
    """
    Manages computational attention budget.
    System has limited resources for deep analysis.
    """
    
    def __init__(self, max_concurrent_analyses: int = 5, 
                 analysis_time_budget_ms: int = 1000):
        self.max_concurrent = max_concurrent_analyses
        self.time_budget_ms = analysis_time_budget_ms
        self.current_analyses: Set[str] = set()
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.budget_consumed_ms = 0
        self.cycle_start = datetime.now(timezone.utc)
    
    async def allocate_attention(self, observation: Observation) -> bool:
        """
        Decide if this observation deserves deep analysis.
        Priority scoring based on anomaly potential.
        """
        # Reset budget every minute
        now = datetime.now(timezone.utc)
        if (now - self.cycle_start).total_seconds() > 60:
            self.budget_consumed_ms = 0
            self.cycle_start = now
        
        # Priority factors
        priority_score = 0.0
        
        # Error events get high priority
        if observation.status in ["error", "failure", "timeout"]:
            priority_score += 0.5
        
        # Slow operations get medium priority
        if observation.duration_ms > 1000:  # > 1 second
            priority_score += 0.3
        
        # Unusual time patterns get medium priority
        hour = observation.timestamp.hour
        if hour < 6 or hour > 22:  # Off-hours
            priority_score += 0.2
        
        # Check budget
        if len(self.current_analyses) >= self.max_concurrent:
            # Queue for later if high priority
            if priority_score > 0.6:
                await self.analysis_queue.put(observation)
            return False
        
        if self.budget_consumed_ms >= self.time_budget_ms:
            return False
        
        # Allocate
        self.current_analyses.add(observation.observation_id)
        return True
    
    def release_attention(self, observation_id: str, time_consumed_ms: int):
        """Release attention allocation."""
        self.current_analyses.discard(observation_id)
        self.budget_consumed_ms += time_consumed_ms


class MetacognitiveEngine:
    """
    Core metacognitive engine that powers the autonomy layer.
    
    Implements the OODA loop: Observe → Orient → Decide → Act
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self.db_pool = db_pool
        self.cognitive_budget = CognitiveBudget()
        self.learned_patterns: Dict[str, Pattern] = {}
        self.active_predictions: Dict[str, Prediction] = {}
        self.observation_buffer: List[Observation] = []
        self.is_running = False
        self._observation_task: Optional[asyncio.Task] = None
        self._analysis_task: Optional[asyncio.Task] = None
        
        # Event subscribers
        self._subscribers: List[callable] = []
    
    async def initialize(self):
        """Initialize database connections and load learned patterns."""
        if not self.db_pool:
            # Connect to existing Postgres
            db_url = os.getenv("METACOGNITIVE_DB_URL", "postgresql://localhost:5435/metacognitive")
            self.db_pool = await asyncpg.create_pool(db_url)
        
        # Ensure tables exist
        await self._ensure_schema()
        
        # Load existing patterns
        await self._load_patterns()
        
        print("✅ Metacognitive Engine initialized")
    
    async def _ensure_schema(self):
        """Create database tables if they don't exist."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    service VARCHAR(64),
                    operation VARCHAR(128),
                    duration_ms INTEGER,
                    status VARCHAR(32),
                    metadata JSONB,
                    context_hash VARCHAR(64)
                );
                
                CREATE INDEX IF NOT EXISTS idx_telemetry_time 
                    ON telemetry_events(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_telemetry_service 
                    ON telemetry_events(service);
                CREATE INDEX IF NOT EXISTS idx_telemetry_hash 
                    ON telemetry_events(context_hash);
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    pattern_type VARCHAR(64),
                    signature VARCHAR(256) UNIQUE,
                    context_features JSONB,
                    success_rate FLOAT DEFAULT 0.5,
                    avg_duration_ms INTEGER,
                    first_seen TIMESTAMPTZ DEFAULT NOW(),
                    last_seen TIMESTAMPTZ DEFAULT NOW(),
                    occurrence_count INTEGER DEFAULT 0,
                    confidence_score FLOAT DEFAULT 0.0
                );
                
                CREATE INDEX IF NOT EXISTS idx_pattern_signature 
                    ON learned_patterns(signature);
                CREATE INDEX IF NOT EXISTS idx_pattern_confidence 
                    ON learned_patterns(confidence_score DESC);
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    predicted_at TIMESTAMPTZ DEFAULT NOW(),
                    prediction_type VARCHAR(64),
                    confidence FLOAT,
                    predicted_action JSONB,
                    trigger_features JSONB,
                    actual_outcome JSONB,
                    was_correct BOOLEAN,
                    user_confirmed BOOLEAN
                );
                
                CREATE INDEX IF NOT EXISTS idx_predictions_time 
                    ON predictions(predicted_at DESC);
            """)
    
    async def _load_patterns(self):
        """Load previously learned patterns from database."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM learned_patterns 
                WHERE confidence_score > 0.3
                ORDER BY confidence_score DESC
                LIMIT 1000
            """)
            
            for row in rows:
                pattern = Pattern(
                    pattern_id=str(row['id']),
                    pattern_type=row['pattern_type'],
                    signature=row['signature'],
                    context_features=row['context_features'],
                    success_rate=row['success_rate'],
                    avg_duration_ms=row['avg_duration_ms'],
                    occurrence_count=row['occurrence_count'],
                    first_seen=row['first_seen'],
                    last_seen=row['last_seen'],
                    confidence_score=row['confidence_score']
                )
                self.learned_patterns[pattern.signature] = pattern
        
        print(f"📚 Loaded {len(self.learned_patterns)} learned patterns")
    
    def subscribe(self, callback: callable):
        """Subscribe to autonomy decisions."""
        self._subscribers.append(callback)
    
    async def observe(self, event_data: Dict[str, Any]):
        """
        Ingest a system event for observation.
        
        This is the entry point for all telemetry.
        """
        observation = Observation(
            observation_id=event_data.get('id') or self._generate_id(),
            timestamp=datetime.now(timezone.utc),
            service=event_data.get('service', 'unknown'),
            operation=event_data.get('operation', 'unknown'),
            duration_ms=event_data.get('duration_ms', 0),
            status=event_data.get('status', 'unknown'),
            metadata=event_data.get('metadata', {}),
            context_hash=""
        )
        observation.context_hash = observation.compute_signature()
        
        # Buffer for batch processing
        self.observation_buffer.append(observation)
        
        # Immediate pattern matching for critical events
        if observation.status in ['error', 'failure']:
            await self._handle_critical_observation(observation)
    
    async def _handle_critical_observation(self, obs: Observation):
        """Fast-path for critical events."""
        # Check if this matches a known failure pattern
        if obs.context_hash in self.learned_patterns:
            pattern = self.learned_patterns[obs.context_hash]
            if pattern.confidence_score > 0.7:
                # Known pattern with good recovery rate
                await self._notify_subscribers({
                    'type': 'critical_pattern_matched',
                    'observation': obs,
                    'pattern': pattern,
                    'suggested_action': 'auto_remediate'
                })
    
    async def start_observation_loop(self, interval_seconds: float = 30.0):
        """Start continuous observation and learning loops."""
        self.is_running = True
        
        # Start observation processor
        self._observation_task = asyncio.create_task(
            self._observation_processor_loop(interval_seconds)
        )
        
        # Start pattern analyzer
        self._analysis_task = asyncio.create_task(
            self._pattern_analysis_loop(interval_seconds * 2)
        )
        
        print(f"🧠 Metacognitive loops started (interval: {interval_seconds}s)")
    
    async def _observation_processor_loop(self, interval: float):
        """Process buffered observations."""
        while self.is_running:
            try:
                if self.observation_buffer:
                    await self._flush_observation_buffer()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"⚠️ Observation processor error: {e}")
                await asyncio.sleep(5)
    
    async def _flush_observation_buffer(self):
        """Persist observations and update patterns."""
        if not self.observation_buffer:
            return
        
        batch = self.observation_buffer[:100]  # Process in chunks
        self.observation_buffer = self.observation_buffer[100:]
        
        # Persist to database
        async with self.db_pool.acquire() as conn:
            for obs in batch:
                await conn.execute("""
                    INSERT INTO telemetry_events 
                    (id, timestamp, service, operation, duration_ms, status, metadata, context_hash)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                    obs.observation_id, obs.timestamp, obs.service,
                    obs.operation, obs.duration_ms, obs.status,
                    json.dumps(obs.metadata), obs.context_hash
                )
                
                # Update or create pattern
                await self._upsert_pattern(obs)
        
        print(f"💾 Persisted {len(batch)} observations")
    
    async def _upsert_pattern(self, obs: Observation):
        """Update pattern statistics."""
        success = obs.status in ['success', 'completed']
        
        if obs.context_hash in self.learned_patterns:
            pattern = self.learned_patterns[obs.context_hash]
            pattern.update_confidence(success, obs.duration_ms)
            
            # Update DB
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE learned_patterns 
                    SET success_rate = $1, 
                        avg_duration_ms = $2,
                        occurrence_count = $3,
                        last_seen = NOW(),
                        confidence_score = $4
                    WHERE signature = $5
                """,
                    pattern.success_rate, pattern.avg_duration_ms,
                    pattern.occurrence_count, pattern.confidence_score,
                    obs.context_hash
                )
        else:
            # Create new pattern
            pattern = Pattern(
                pattern_id=self._generate_id(),
                pattern_type=self._infer_pattern_type(obs),
                signature=obs.context_hash,
                context_features={
                    'service': obs.service,
                    'operation': obs.operation,
                    'hour': obs.timestamp.hour
                },
                success_rate=1.0 if success else 0.0,
                avg_duration_ms=obs.duration_ms,
                occurrence_count=1,
                first_seen=obs.timestamp,
                last_seen=obs.timestamp,
                confidence_score=0.1
            )
            self.learned_patterns[obs.context_hash] = pattern
            
            # Insert to DB
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO learned_patterns 
                    (pattern_type, signature, context_features, success_rate,
                     avg_duration_ms, occurrence_count, confidence_score)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (signature) DO NOTHING
                """,
                    pattern.pattern_type, pattern.signature,
                    json.dumps(pattern.context_features),
                    pattern.success_rate, pattern.avg_duration_ms,
                    pattern.occurrence_count, pattern.confidence_score
                )
    
    def _infer_pattern_type(self, obs: Observation) -> str:
        """Categorize the pattern type."""
        if obs.status in ['error', 'failure']:
            return 'error_pattern'
        elif obs.duration_ms > 1000:
            return 'slow_operation'
        elif obs.service in ['money', 'cleardesk']:
            return 'business_operation'
        return 'general_api_call'
    
    async def _pattern_analysis_loop(self, interval: float):
        """Deep analysis of patterns for predictions."""
        while self.is_running:
            try:
                await self._generate_predictions()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"⚠️ Pattern analysis error: {e}")
                await asyncio.sleep(10)
    
    async def _generate_predictions(self):
        """Generate predictions based on learned patterns."""
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # Look for temporal patterns
        predictions_made = 0
        
        for signature, pattern in self.learned_patterns.items():
            if pattern.confidence_score < 0.5:
                continue
            
            # Time-based prediction
            if pattern.occurrence_count > 10:
                hour_matches = sum(
                    1 for _ in range(pattern.occurrence_count)
                    if pattern.context_features.get('hour') == hour
                )
                if hour_matches / pattern.occurrence_count > 0.8:
                    # High probability this operation will occur
                    prediction = Prediction(
                        prediction_id=self._generate_id(),
                        predicted_at=now,
                        prediction_type='likely_operation',
                        confidence=pattern.confidence_score * 0.8,
                        predicted_action={
                            'service': pattern.context_features.get('service'),
                            'operation': pattern.context_features.get('operation'),
                            'preparation': 'warm_cache'
                        },
                        trigger_features={'hour': hour, 'pattern_signature': signature}
                    )
                    
                    self.active_predictions[prediction.prediction_id] = prediction
                    predictions_made += 1
                    
                    # Notify if actionable
                    if prediction.is_actionable():
                        await self._notify_subscribers({
                            'type': 'prediction',
                            'prediction': prediction,
                            'action': 'prepare_resources'
                        })
        
        if predictions_made > 0:
            print(f"🔮 Generated {predictions_made} predictions")
    
    async def _notify_subscribers(self, event: Dict[str, Any]):
        """Notify all subscribers of autonomy event."""
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"⚠️ Subscriber error: {e}")
    
    def get_insights(self) -> Dict[str, Any]:
        """Get current metacognitive insights."""
        if not self.learned_patterns:
            return {'status': 'learning', 'patterns': 0}
        
        # Compute statistics
        confidences = [p.confidence_score for p in self.learned_patterns.values()]
        success_rates = [p.success_rate for p in self.learned_patterns.values()]
        
        return {
            'status': 'active',
            'patterns_learned': len(self.learned_patterns),
            'avg_confidence': statistics.mean(confidences) if confidences else 0,
            'high_confidence_patterns': sum(1 for c in confidences if c > 0.8),
            'avg_success_rate': statistics.mean(success_rates) if success_rates else 0,
            'active_predictions': len(self.active_predictions),
            'observation_buffer_size': len(self.observation_buffer),
            'cognitive_budget_consumed_ms': self.cognitive_budget.budget_consumed_ms,
        }
    
    async def stop(self):
        """Stop the metacognitive engine."""
        self.is_running = False
        
        if self._observation_task:
            self._observation_task.cancel()
        if self._analysis_task:
            self._analysis_task.cancel()
        
        # Flush remaining observations
        await self._flush_observation_buffer()
        
        if self.db_pool:
            await self.db_pool.close()
        
        print("🛑 Metacognitive Engine stopped")
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        import uuid
        return str(uuid.uuid4())


# Singleton instance
_engine: Optional[MetacognitiveEngine] = None


async def get_engine() -> MetacognitiveEngine:
    """Get or create the singleton metacognitive engine."""
    global _engine
    if _engine is None:
        _engine = MetacognitiveEngine()
        await _engine.initialize()
    return _engine
