"""
Feedback Loop System for Continuous Learning

Captures success/failure signals from every system interaction and
feeds them into the learning pipeline.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

import asyncpg


class FeedbackType(Enum):
    """Types of feedback signals."""
    SUCCESS = "success"           # Task completed as expected
    PARTIAL = "partial"           # Task completed with workarounds
    FAILURE = "failure"           # Task failed, manual intervention required
    TIMEOUT = "timeout"           # Task exceeded time budget
    EXCEPTION = "exception"       # Unexpected error occurred
    USER_CORRECTION = "user_correction"  # User had to manually fix output
    OPTIMIZATION = "optimization" # Task ran slower than baseline
    CANCELLATION = "cancellation" # User cancelled the task
    POSITIVE_REINFORCEMENT = "positive"  # Explicit user praise
    NEGATIVE_REINFORCEMENT = "negative"  # Explicit user complaint


@dataclass
class FeedbackSignal:
    """
    A single feedback signal from any system component.
    """
    signal_id: str
    timestamp: datetime
    source_service: str
    source_operation: str
    feedback_type: FeedbackType
    
    # Context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # What happened
    input_context: Dict[str, Any] = field(default_factory=dict)
    output_result: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    duration_ms: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    
    # Feedback specifics
    expectation_gap: Optional[str] = None  # What was expected vs what happened
    correction_applied: Optional[Dict[str, Any]] = None  # How user fixed it
    satisfaction_score: Optional[int] = None  # 1-10 if provided
    
    # Learning metadata
    decision_path: List[str] = field(default_factory=list)  # Chain of decisions made
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # Tools used
    agent_reasoning: Optional[str] = None  # Agent's explanation
    
    def compute_learning_vector(self) -> Dict[str, Any]:
        """
        Convert feedback into a feature vector for learning.
        """
        # Success weight by feedback type
        success_weights = {
            FeedbackType.SUCCESS: 1.0,
            FeedbackType.POSITIVE_REINFORCEMENT: 1.0,
            FeedbackType.PARTIAL: 0.5,
            FeedbackType.OPTIMIZATION: 0.3,
            FeedbackType.CANCELLATION: 0.0,
            FeedbackType.TIMEOUT: -0.5,
            FeedbackType.FAILURE: -1.0,
            FeedbackType.EXCEPTION: -1.0,
            FeedbackType.USER_CORRECTION: -0.8,
            FeedbackType.NEGATIVE_REINFORCEMENT: -1.0,
        }
        
        # Time-of-day features
        hour = self.timestamp.hour
        time_features = {
            'is_business_hours': 9 <= hour < 17,
            'is_peak_hours': 10 <= hour < 12 or 14 <= hour < 16,
            'is_off_hours': hour < 6 or hour > 22,
        }
        
        # Performance features
        perf_features = {
            'duration_ms': self.duration_ms,
            'is_slow': self.duration_ms > 1000,
            'is_very_slow': self.duration_ms > 5000,
        }
        
        # Decision path fingerprint
        path_hash = hashlib.sha256(
            ','.join(self.decision_path).encode()
        ).hexdigest()[:16] if self.decision_path else "none"
        
        return {
            'success_score': success_weights.get(self.feedback_type, 0),
            'feedback_type': self.feedback_type.value,
            'service': self.source_service,
            'operation': self.source_operation,
            'path_hash': path_hash,
            'tool_count': len(self.tool_calls),
            **time_features,
            **perf_features,
        }


@dataclass
class LearnedInsight:
    """
    An insight extracted from accumulated feedback.
    """
    insight_id: str
    insight_type: str  # "successful_path", "failure_pattern", "optimization_opportunity"
    
    # What we learned
    trigger_conditions: Dict[str, Any]  # When does this apply
    recommended_action: Dict[str, Any]  # What to do
    
    # Confidence metrics
    supporting_evidence_count: int
    success_rate: float
    confidence_score: float
    
    # Metadata
    first_observed: datetime
    last_validated: datetime
    is_active: bool = True
    
    def should_apply(self, context: Dict[str, Any]) -> float:
        """
        Check if this insight applies to current context.
        Returns confidence score (0-1).
        """
        match_score = 0.0
        total_weight = 0.0
        
        for key, expected_value in self.trigger_conditions.items():
            if key in context:
                total_weight += 1.0
                actual_value = context[key]
                
                if isinstance(expected_value, (list, tuple)):
                    if actual_value in expected_value:
                        match_score += 1.0
                elif expected_value == actual_value:
                    match_score += 1.0
                elif isinstance(expected_value, float):
                    # Fuzzy match for numeric values
                    if abs(expected_value - actual_value) / expected_value < 0.1:
                        match_score += 0.8
        
        if total_weight == 0:
            return 0.0
        
        return (match_score / total_weight) * self.confidence_score


class FeedbackCollector:
    """
    Collects, processes, and learns from feedback signals across all systems.
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self.db_pool = db_pool
        self._feedback_buffer: List[FeedbackSignal] = []
        self._learned_insights: Dict[str, LearnedInsight] = {}
        self._on_insight_callbacks: List[Callable] = []
        self._is_running = False
        self._processing_task: Optional[asyncio.Task] = None
        
        # Processing configuration
        self.batch_size = 100
        self.processing_interval_seconds = 60
        self.min_evidence_threshold = 5  # Need at least 5 samples for insight
    
    async def initialize(self):
        """Initialize database and load existing insights."""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                "postgresql://localhost:5435/metacognitive"
            )
        
        await self._ensure_schema()
        await self._load_insights()
        
        print("✅ Feedback Collector initialized")
    
    async def _ensure_schema(self):
        """Create feedback tables."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_signals (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    source_service VARCHAR(64),
                    source_operation VARCHAR(128),
                    feedback_type VARCHAR(32),
                    user_id VARCHAR(128),
                    session_id VARCHAR(128),
                    correlation_id VARCHAR(128),
                    input_context JSONB,
                    output_result JSONB,
                    duration_ms FLOAT,
                    resource_usage JSONB,
                    expectation_gap TEXT,
                    correction_applied JSONB,
                    satisfaction_score INTEGER,
                    decision_path JSONB,
                    tool_calls JSONB,
                    agent_reasoning TEXT,
                    learning_vector JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_feedback_time 
                    ON feedback_signals(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_feedback_service 
                    ON feedback_signals(source_service);
                CREATE INDEX IF NOT EXISTS idx_feedback_type 
                    ON feedback_signals(feedback_type);
                CREATE INDEX IF NOT EXISTS idx_feedback_correlation 
                    ON feedback_signals(correlation_id);
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_insights (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    insight_type VARCHAR(64),
                    trigger_conditions JSONB,
                    recommended_action JSONB,
                    supporting_evidence_count INTEGER DEFAULT 0,
                    success_rate FLOAT DEFAULT 0.0,
                    confidence_score FLOAT DEFAULT 0.0,
                    first_observed TIMESTAMPTZ DEFAULT NOW(),
                    last_validated TIMESTAMPTZ DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE
                );
                
                CREATE INDEX IF NOT EXISTS idx_insights_type 
                    ON learned_insights(insight_type);
                CREATE INDEX IF NOT EXISTS idx_insights_active 
                    ON learned_insights(is_active) WHERE is_active = TRUE;
            """)
    
    async def _load_insights(self):
        """Load previously learned insights."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM learned_insights 
                WHERE is_active = TRUE
                AND confidence_score > 0.3
                ORDER BY confidence_score DESC
            """)
            
            for row in rows:
                insight = LearnedInsight(
                    insight_id=str(row['id']),
                    insight_type=row['insight_type'],
                    trigger_conditions=row['trigger_conditions'],
                    recommended_action=row['recommended_action'],
                    supporting_evidence_count=row['supporting_evidence_count'],
                    success_rate=row['success_rate'],
                    confidence_score=row['confidence_score'],
                    first_observed=row['first_observed'],
                    last_validated=row['last_validated'],
                    is_active=row['is_active']
                )
                self._learned_insights[insight.insight_id] = insight
        
        print(f"📚 Loaded {len(self._learned_insights)} learned insights")
    
    def on_new_insight(self, callback: Callable):
        """Subscribe to new insight discoveries."""
        self._on_insight_callbacks.append(callback)
    
    async def collect_feedback(self, 
                              source_service: str,
                              source_operation: str,
                              feedback_type: Union[FeedbackType, str],
                              **kwargs) -> str:
        """
        Collect feedback from any system component.
        
        Returns signal_id for correlation.
        """
        import uuid
        
        if isinstance(feedback_type, str):
            feedback_type = FeedbackType(feedback_type)
        
        signal = FeedbackSignal(
            signal_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc),
            source_service=source_service,
            source_operation=source_operation,
            feedback_type=feedback_type,
            user_id=kwargs.get('user_id'),
            session_id=kwargs.get('session_id'),
            correlation_id=kwargs.get('correlation_id'),
            input_context=kwargs.get('input_context', {}),
            output_result=kwargs.get('output_result', {}),
            duration_ms=kwargs.get('duration_ms', 0),
            resource_usage=kwargs.get('resource_usage', {}),
            expectation_gap=kwargs.get('expectation_gap'),
            correction_applied=kwargs.get('correction_applied'),
            satisfaction_score=kwargs.get('satisfaction_score'),
            decision_path=kwargs.get('decision_path', []),
            tool_calls=kwargs.get('tool_calls', []),
            agent_reasoning=kwargs.get('agent_reasoning')
        )
        
        # Buffer for batch processing
        self._feedback_buffer.append(signal)
        
        # Immediate processing for critical feedback
        if feedback_type in [FeedbackType.FAILURE, FeedbackType.EXCEPTION]:
            await self._process_critical_feedback(signal)
        
        return signal.signal_id
    
    async def _process_critical_feedback(self, signal: FeedbackSignal):
        """Immediate processing for critical failures."""
        print(f"🚨 Critical feedback: {signal.source_service}.{signal.source_operation}")
        
        # Persist immediately
        await self._persist_feedback([signal])
        
        # Check for failure patterns
        similar_failures = await self._find_similar_failures(signal)
        if len(similar_failures) >= 3:
            # Emerging pattern detected
            await self._create_failure_pattern_insight(signal, similar_failures)
    
    async def _find_similar_failures(self, signal: FeedbackSignal) -> List[Dict]:
        """Find similar recent failures."""
        async with self.db_pool.acquire() as conn:
            # Look for same service/operation with failure in last hour
            rows = await conn.fetch("""
                SELECT * FROM feedback_signals
                WHERE source_service = $1
                AND source_operation = $2
                AND feedback_type IN ('failure', 'exception')
                AND timestamp > NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC
                LIMIT 10
            """, signal.source_service, signal.source_operation)
            
            return [dict(row) for row in rows]
    
    async def _create_failure_pattern_insight(self, signal: FeedbackSignal, 
                                              similar: List[Dict]):
        """Create insight from emerging failure pattern."""
        import uuid
        
        insight = LearnedInsight(
            insight_id=str(uuid.uuid4())[:8],
            insight_type="failure_pattern",
            trigger_conditions={
                'service': signal.source_service,
                'operation': signal.source_operation,
                'recent_failures': len(similar)
            },
            recommended_action={
                'action': 'circuit_breaker',
                'escalate': True,
                'message': f"Emerging failure pattern detected: {len(similar)} similar failures"
            },
            supporting_evidence_count=len(similar),
            success_rate=0.0,  # This is about avoiding failures
            confidence_score=min(0.9, len(similar) / 10),
            first_observed=signal.timestamp,
            last_validated=datetime.now(timezone.utc)
        )
        
        self._learned_insights[insight.insight_id] = insight
        await self._persist_insight(insight)
        
        # Notify subscribers
        for callback in self._on_insight_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(insight)
                else:
                    callback(insight)
            except Exception as e:
                print(f"⚠️ Insight callback error: {e}")
    
    async def start_processing_loop(self):
        """Start batch processing of feedback."""
        self._is_running = True
        self._processing_task = asyncio.create_task(
            self._processing_loop()
        )
        print("🔄 Feedback processing loop started")
    
    async def _processing_loop(self):
        """Background processing of feedback buffer."""
        while self._is_running:
            try:
                await asyncio.sleep(self.processing_interval_seconds)
                
                if self._feedback_buffer:
                    await self._process_feedback_batch()
                    
            except Exception as e:
                print(f"⚠️ Feedback processing error: {e}")
    
    async def _process_feedback_batch(self):
        """Process buffered feedback."""
        if not self._feedback_buffer:
            return
        
        batch = self._feedback_buffer[:self.batch_size]
        self._feedback_buffer = self._feedback_buffer[self.batch_size:]
        
        # Persist to database
        await self._persist_feedback(batch)
        
        # Extract insights
        await self._extract_insights_from_batch(batch)
        
        print(f"📊 Processed {len(batch)} feedback signals")
    
    async def _persist_feedback(self, signals: List[FeedbackSignal]):
        """Persist feedback signals to database."""
        async with self.db_pool.acquire() as conn:
            for signal in signals:
                learning_vector = signal.compute_learning_vector()
                
                await conn.execute("""
                    INSERT INTO feedback_signals 
                    (source_service, source_operation, feedback_type, user_id,
                     session_id, correlation_id, input_context, output_result,
                     duration_ms, resource_usage, expectation_gap, correction_applied,
                     satisfaction_score, decision_path, tool_calls, agent_reasoning,
                     learning_vector)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                """,
                    signal.source_service,
                    signal.source_operation,
                    signal.feedback_type.value,
                    signal.user_id,
                    signal.session_id,
                    signal.correlation_id,
                    json.dumps(signal.input_context),
                    json.dumps(signal.output_result),
                    signal.duration_ms,
                    json.dumps(signal.resource_usage),
                    signal.expectation_gap,
                    json.dumps(signal.correction_applied) if signal.correction_applied else None,
                    signal.satisfaction_score,
                    json.dumps(signal.decision_path),
                    json.dumps(signal.tool_calls),
                    signal.agent_reasoning,
                    json.dumps(learning_vector)
                )
    
    async def _extract_insights_from_batch(self, signals: List[FeedbackSignal]):
        """Extract new insights from feedback batch."""
        # Group by service/operation
        grouped = {}
        for signal in signals:
            key = (signal.source_service, signal.source_operation)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(signal)
        
        # Analyze each group
        for (service, operation), group_signals in grouped.items():
            await self._analyze_service_operation(service, operation, group_signals)
    
    async def _analyze_service_operation(self, service: str, operation: str,
                                        signals: List[FeedbackSignal]):
        """Analyze feedback for a specific service operation."""
        # Count feedback types
        type_counts = {}
        for s in signals:
            type_counts[s.feedback_type] = type_counts.get(s.feedback_type, 0) + 1
        
        # Check for optimization opportunities (many slow operations)
        slow_ops = [s for s in signals 
                   if s.feedback_type == FeedbackType.SUCCESS and s.duration_ms > 1000]
        
        if len(slow_ops) >= 3:
            # Potential optimization insight
            await self._create_optimization_insight(service, operation, slow_ops)
        
        # Check for successful patterns
        success_signals = [s for s in signals if s.feedback_type == FeedbackType.SUCCESS]
        if len(success_signals) >= self.min_evidence_threshold:
            await self._create_success_pattern_insight(service, operation, success_signals)
    
    async def _create_optimization_insight(self, service: str, operation: str,
                                        slow_signals: List[FeedbackSignal]):
        """Create insight about optimization opportunity."""
        import uuid
        
        avg_duration = sum(s.duration_ms for s in slow_signals) / len(slow_signals)
        
        insight = LearnedInsight(
            insight_id=str(uuid.uuid4())[:8],
            insight_type="optimization_opportunity",
            trigger_conditions={
                'service': service,
                'operation': operation,
                'duration_threshold_ms': 1000
            },
            recommended_action={
                'action': 'optimize',
                'suggestion': f'Operation averaging {avg_duration:.0f}ms, consider caching or async',
                'priority': 'medium'
            },
            supporting_evidence_count=len(slow_signals),
            success_rate=1.0,  # These succeeded but were slow
            confidence_score=0.6,
            first_observed=slow_signals[0].timestamp,
            last_validated=datetime.now(timezone.utc)
        )
        
        self._learned_insights[insight.insight_id] = insight
        await self._persist_insight(insight)
    
    async def _create_success_pattern_insight(self, service: str, operation: str,
                                             success_signals: List[FeedbackSignal]):
        """Create insight about what leads to success."""
        import uuid
        
        # Find common decision paths
        path_counts = {}
        for s in success_signals:
            path_key = tuple(s.decision_path)
            path_counts[path_key] = path_counts.get(path_key, 0) + 1
        
        if not path_counts:
            return
        
        # Most common successful path
        best_path = max(path_counts.items(), key=lambda x: x[1])
        
        insight = LearnedInsight(
            insight_id=str(uuid.uuid4())[:8],
            insight_type="successful_path",
            trigger_conditions={
                'service': service,
                'operation': operation,
                'decision_path': list(best_path[0])
            },
            recommended_action={
                'action': 'prefer_path',
                'decision_path': list(best_path[0]),
                'success_rate': best_path[1] / len(success_signals)
            },
            supporting_evidence_count=best_path[1],
            success_rate=best_path[1] / len(success_signals),
            confidence_score=best_path[1] / len(success_signals),
            first_observed=success_signals[0].timestamp,
            last_validated=datetime.now(timezone.utc)
        )
        
        self._learned_insights[insight.insight_id] = insight
        await self._persist_insight(insight)
    
    async def _persist_insight(self, insight: LearnedInsight):
        """Persist insight to database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO learned_insights 
                (insight_type, trigger_conditions, recommended_action,
                 supporting_evidence_count, success_rate, confidence_score,
                 first_observed, last_validated, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    supporting_evidence_count = EXCLUDED.supporting_evidence_count,
                    success_rate = EXCLUDED.success_rate,
                    confidence_score = EXCLUDED.confidence_score,
                    last_validated = EXCLUDED.last_validated
            """,
                insight.insight_type,
                json.dumps(insight.trigger_conditions),
                json.dumps(insight.recommended_action),
                insight.supporting_evidence_count,
                insight.success_rate,
                insight.confidence_score,
                insight.first_observed,
                insight.last_validated,
                insight.is_active
            )
    
    def get_applicable_insights(self, context: Dict[str, Any]) -> List[LearnedInsight]:
        """
        Get insights applicable to current context, sorted by relevance.
        """
        scored_insights = []
        
        for insight in self._learned_insights.values():
            if not insight.is_active:
                continue
            
            score = insight.should_apply(context)
            if score > 0.5:  # Minimum relevance threshold
                scored_insights.append((score, insight))
        
        # Sort by score descending
        scored_insights.sort(key=lambda x: x[0], reverse=True)
        
        return [insight for _, insight in scored_insights[:5]]  # Top 5
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        active_insights = [i for i in self._learned_insights.values() if i.is_active]
        
        return {
            'total_insights': len(self._learned_insights),
            'active_insights': len(active_insights),
            'insights_by_type': self._count_by_type(active_insights),
            'avg_confidence': sum(i.confidence_score for i in active_insights) / len(active_insights) if active_insights else 0,
            'feedback_buffer_size': len(self._feedback_buffer),
            'high_confidence_insights': sum(1 for i in active_insights if i.confidence_score > 0.8),
        }
    
    def _count_by_type(self, insights: List[LearnedInsight]) -> Dict[str, int]:
        """Count insights by type."""
        counts = {}
        for i in insights:
            counts[i.insight_type] = counts.get(i.insight_type, 0) + 1
        return counts
    
    async def stop(self):
        """Stop processing and flush buffer."""
        self._is_running = False
        
        if self._processing_task:
            self._processing_task.cancel()
        
        # Flush remaining feedback
        if self._feedback_buffer:
            await self._process_feedback_batch()
        
        if self.db_pool:
            await self.db_pool.close()
        
        print("🛑 Feedback Collector stopped")


# Convenience methods for easy integration

async def report_success(service: str, operation: str, **kwargs) -> str:
    """Report successful operation."""
    collector = await get_collector()
    return await collector.collect_feedback(
        service, operation, FeedbackType.SUCCESS, **kwargs
    )

async def report_failure(service: str, operation: str, error: str, **kwargs) -> str:
    """Report failed operation."""
    collector = await get_collector()
    return await collector.collect_feedback(
        service, operation, FeedbackType.FAILURE, 
        expectation_gap=error, **kwargs
    )

async def report_user_correction(service: str, operation: str, 
                                original: Any, corrected: Any, **kwargs) -> str:
    """Report that user had to correct system output."""
    collector = await get_collector()
    return await collector.collect_feedback(
        service, operation, FeedbackType.USER_CORRECTION,
        expectation_gap=f"Expected: {corrected}, Got: {original}",
        correction_applied={'from': original, 'to': corrected},
        **kwargs
    )


# Singleton
_collector: Optional[FeedbackCollector] = None


async def get_collector() -> FeedbackCollector:
    """Get or create singleton collector."""
    global _collector
    if _collector is None:
        _collector = FeedbackCollector()
        await _collector.initialize()
    return _collector
