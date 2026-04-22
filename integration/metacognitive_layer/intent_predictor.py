"""
JIT Intent Prediction Engine

Anticipates user needs and system requirements before they're articulated.
Pre-warms resources and prepares actions for likely future events.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

import asyncpg


class PredictionType(Enum):
    """Types of predictions the engine can make."""
    USER_INTENT = "user_intent"           # What user will likely do next
    LOAD_SPIKE = "load_spike"             # Incoming traffic surge
    RESOURCE_NEED = "resource_need"       # Will need more capacity
    OPTIMAL_ROUTE = "optimal_route"       # Best system to handle request
    CACHE_OPPORTUNITY = "cache_opportunity"  # Data likely to be needed
    FAILURE_RISK = "failure_risk"         # Service likely to fail


@dataclass
class IntentPrediction:
    """A single prediction about future state."""
    prediction_id: str
    predicted_at: datetime
    prediction_type: PredictionType
    confidence: float  # 0.0 - 1.0
    
    # What is predicted
    predicted_event: str
    predicted_action: Dict[str, Any]
    trigger_features: Dict[str, Any]
    
    # When
    expected_in_seconds: Optional[int] = None
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    
    # Preparation
    preparation_action: Optional[str] = None
    preparation_params: Dict[str, Any] = None
    
    # Outcome tracking
    actual_outcome: Optional[str] = None
    outcome_validated_at: Optional[datetime] = None
    was_correct: Optional[bool] = None
    
    def is_actionable(self) -> Tuple[bool, str]:
        """
        Determine if prediction should trigger autonomous action.
        Returns (should_act, reason).
        """
        if self.confidence >= 0.95:
            return True, "Critical confidence - execute automatically"
        elif self.confidence >= 0.85:
            return True, "High confidence - execute with notification"
        elif self.confidence >= 0.70:
            return False, "Medium confidence - prepare only, ask confirmation"
        else:
            return False, "Low confidence - observe only"
    
    def to_preparation_command(self) -> Optional[Dict[str, Any]]:
        """Convert prediction to preparation command."""
        if not self.preparation_action:
            return None
        
        return {
            'action': self.preparation_action,
            'params': self.preparation_params or {},
            'confidence': self.confidence,
            'prediction_id': self.prediction_id,
            'predicted_event': self.predicted_event
        }


class TemporalPatternAnalyzer:
    """Analyzes time-based patterns in user/system behavior."""
    
    def __init__(self):
        self.hourly_patterns: Dict[str, Dict[int, int]] = {}  # service -> hour -> count
        self.daily_patterns: Dict[str, Dict[int, int]] = {}  # service -> day -> count
        self.sequences: Dict[str, List[str]] = {}  # action -> likely_next_actions
    
    def record_activity(self, service: str, operation: str, timestamp: datetime):
        """Record an activity for pattern analysis."""
        if service not in self.hourly_patterns:
            self.hourly_patterns[service] = {}
        if service not in self.daily_patterns:
            self.daily_patterns[service] = {}
        
        hour = timestamp.hour
        day = timestamp.weekday()
        
        self.hourly_patterns[service][hour] = self.hourly_patterns[service].get(hour, 0) + 1
        self.daily_patterns[service][day] = self.daily_patterns[service].get(day, 0) + 1
    
    def predict_next_hour_activity(self, service: str, hour: int) -> float:
        """Predict how likely service is to be active in given hour."""
        if service not in self.hourly_patterns:
            return 0.5
        
        hour_counts = self.hourly_patterns[service]
        total = sum(hour_counts.values())
        
        if total == 0:
            return 0.5
        
        return hour_counts.get(hour, 0) / total
    
    def get_peak_hours(self, service: str) -> List[int]:
        """Get hours with highest activity for a service."""
        if service not in self.hourly_patterns:
            return []
        
        hours = self.hourly_patterns[service]
        max_count = max(hours.values()) if hours else 0
        threshold = max_count * 0.7  # Within 70% of peak
        
        return [h for h, c in hours.items() if c >= threshold]


class IntentPredictor:
    """
    Predicts user intent and system needs for JIT preparation.
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self.db_pool = db_pool
        self.temporal_analyzer = TemporalPatternAnalyzer()
        self.active_predictions: Dict[str, IntentPrediction] = {}
        self._prediction_history: List[IntentPrediction] = []
        self._is_running = False
        self._prediction_task: Optional[asyncio.Task] = None
        self._validation_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize predictor."""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                "postgresql://localhost:5435/metacognitive"
            )
        
        await self._ensure_schema()
        await self._load_historical_patterns()
        
        print("✅ Intent Predictor initialized")
    
    async def _ensure_schema(self):
        """Create prediction tables."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    predicted_at TIMESTAMPTZ DEFAULT NOW(),
                    prediction_type VARCHAR(64),
                    confidence FLOAT,
                    predicted_event VARCHAR(256),
                    predicted_action JSONB,
                    trigger_features JSONB,
                    expected_in_seconds INTEGER,
                    time_window_start TIMESTAMPTZ,
                    time_window_end TIMESTAMPTZ,
                    preparation_action VARCHAR(128),
                    preparation_params JSONB,
                    actual_outcome VARCHAR(256),
                    outcome_validated_at TIMESTAMPTZ,
                    was_correct BOOLEAN
                );
                
                CREATE INDEX IF NOT EXISTS idx_predictions_time 
                    ON predictions(predicted_at DESC);
                CREATE INDEX IF NOT EXISTS idx_predictions_type 
                    ON predictions(prediction_type);
                CREATE INDEX IF NOT EXISTS idx_predictions_validated 
                    ON predictions(was_correct) WHERE was_correct IS NOT NULL;
            """)
    
    async def _load_historical_patterns(self):
        """Load historical activity patterns from database."""
        async with self.db_pool.acquire() as conn:
            # Load recent telemetry
            rows = await conn.fetch("""
                SELECT service, operation, timestamp, context_hash
                FROM telemetry_events
                WHERE timestamp > NOW() - INTERVAL '7 days'
                ORDER BY timestamp
            """)
            
            for row in rows:
                self.temporal_analyzer.record_activity(
                    row['service'], row['operation'], row['timestamp']
                )
        
        print(f"📚 Loaded patterns for {len(self.temporal_analyzer.hourly_patterns)} services")
    
    async def record_activity(self, service: str, operation: str, 
                            context: Optional[Dict[str, Any]] = None):
        """
        Record user/system activity for pattern learning.
        
        This should be called on every meaningful interaction.
        """
        now = datetime.now(timezone.utc)
        
        # Update temporal patterns
        self.temporal_analyzer.record_activity(service, operation, now)
        
        # Generate immediate predictions based on this activity
        await self._generate_contextual_predictions(service, operation, context or {}, now)
    
    async def _generate_contextual_predictions(self, service: str, operation: str,
                                              context: Dict[str, Any], 
                                              timestamp: datetime):
        """Generate predictions based on current activity context."""
        predictions = []
        
        # 1. Time-based prediction
        next_hour = (timestamp.hour + 1) % 24
        hour_likelihood = self.temporal_analyzer.predict_next_hour_activity(service, next_hour)
        
        if hour_likelihood > 0.7:
            pred = IntentPrediction(
                prediction_id=self._generate_id(),
                predicted_at=timestamp,
                prediction_type=PredictionType.LOAD_SPIKE,
                confidence=hour_likelihood,
                predicted_event=f"{service}_peak_hour",
                predicted_action={'hour': next_hour, 'service': service},
                trigger_features={'current_hour': timestamp.hour, 'historical_pattern': True},
                expected_in_seconds=3600,
                preparation_action='pre_scale',
                preparation_params={'service': service, 'replicas': 3}
            )
            predictions.append(pred)
        
        # 2. Operation sequence prediction
        likely_next = self._predict_next_operation(service, operation)
        if likely_next:
            pred = IntentPrediction(
                prediction_id=self._generate_id(),
                predicted_at=timestamp,
                prediction_type=PredictionType.USER_INTENT,
                confidence=likely_next['confidence'],
                predicted_event=likely_next['operation'],
                predicted_action={'service': service, 'operation': likely_next['operation']},
                trigger_features={'previous_operation': operation},
                expected_in_seconds=30,
                preparation_action='warm_cache',
                preparation_params={'service': service, 'operation': likely_next['operation']}
            )
            predictions.append(pred)
        
        # 3. Business logic predictions
        if service == 'cleardesk' and operation == 'login':
            # User likely to check documents after login
            pred = IntentPrediction(
                prediction_id=self._generate_id(),
                predicted_at=timestamp,
                prediction_type=PredictionType.USER_INTENT,
                confidence=0.85,
                predicted_event='document_review',
                predicted_action={'load_dashboard': True, 'pre_fetch': 'recent_docs'},
                trigger_features={'service': 'cleardesk', 'action': 'login'},
                expected_in_seconds=5,
                preparation_action='pre_fetch_data',
                preparation_params={'query': 'recent_documents', 'limit': 20}
            )
            predictions.append(pred)
        
        if service == 'money' and operation == 'dispatch_create':
            # Likely will need technician matching
            pred = IntentPrediction(
                prediction_id=self._generate_id(),
                predicted_at=timestamp,
                prediction_type=PredictionType.OPTIMAL_ROUTE,
                confidence=0.90,
                predicted_event='technician_match',
                predicted_action={'service': 'money', 'operation': 'technician_match'},
                trigger_features={'dispatch_created': True},
                expected_in_seconds=2,
                preparation_action='pre_compute',
                preparation_params={'algorithm': 'nearest_technician', 'radius_miles': 25}
            )
            predictions.append(pred)
        
        # Store and act on predictions
        for pred in predictions:
            self.active_predictions[pred.prediction_id] = pred
            await self._persist_prediction(pred)
            
            should_act, reason = pred.is_actionable()
            if should_act:
                print(f"🔮 Prediction ({pred.confidence:.0%}): {pred.predicted_event} - {reason}")
                # Would trigger preparation here
    
    def _predict_next_operation(self, service: str, current_operation: str) -> Optional[Dict]:
        """Predict next operation based on historical sequences."""
        # This would use sequence analysis from temporal_analyzer
        # For now, use hardcoded common sequences
        
        sequences = {
            ('cleardesk', 'upload'): {'operation': 'process', 'confidence': 0.9},
            ('cleardesk', 'process'): {'operation': 'review', 'confidence': 0.8},
            ('cleardesk', 'review'): {'operation': 'export', 'confidence': 0.7},
            ('money', 'triage'): {'operation': 'dispatch', 'confidence': 0.85},
            ('money', 'dispatch'): {'operation': 'track', 'confidence': 0.9},
            ('b-a-p', 'upload'): {'operation': 'analyze', 'confidence': 0.8},
        }
        
        key = (service, current_operation)
        return sequences.get(key)
    
    async def start_prediction_loop(self, interval_seconds: float = 60.0):
        """Start continuous prediction generation."""
        self._is_running = True
        
        self._prediction_task = asyncio.create_task(
            self._prediction_generation_loop(interval_seconds)
        )
        self._validation_task = asyncio.create_task(
            self._prediction_validation_loop(interval_seconds * 5)
        )
        
        print(f"🔮 Prediction loops started (interval: {interval_seconds}s)")
    
    async def _prediction_generation_loop(self, interval: float):
        """Generate periodic predictions."""
        while self._is_running:
            try:
                await self._generate_temporal_predictions()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"⚠️ Prediction generation error: {e}")
                await asyncio.sleep(10)
    
    async def _generate_temporal_predictions(self):
        """Generate predictions based on temporal patterns."""
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        
        for service in self.temporal_analyzer.hourly_patterns.keys():
            # Predict next hour
            next_hour = (current_hour + 1) % 24
            likelihood = self.temporal_analyzer.predict_next_hour_activity(service, next_hour)
            
            if likelihood > 0.8 and likelihood < 0.99:  # High but not certain
                pred = IntentPrediction(
                    prediction_id=self._generate_id(),
                    predicted_at=now,
                    prediction_type=PredictionType.LOAD_SPIKE,
                    confidence=likelihood,
                    predicted_event=f'{service}_busy_hour',
                    predicted_action={'hour': next_hour},
                    trigger_features={'pattern': 'hourly_peak', 'historical_confidence': likelihood},
                    expected_in_seconds=3600,
                    preparation_action='scale_up',
                    preparation_params={'service': service, 'min_replicas': 2}
                )
                
                self.active_predictions[pred.prediction_id] = pred
                await self._persist_prediction(pred)
    
    async def _prediction_validation_loop(self, interval: float):
        """Validate past predictions against actual outcomes."""
        while self._is_running:
            try:
                await asyncio.sleep(interval)
                await self._validate_pending_predictions()
            except Exception as e:
                print(f"⚠️ Prediction validation error: {e}")
    
    async def _validate_pending_predictions(self):
        """Check if predictions came true."""
        now = datetime.now(timezone.utc)
        
        # Find predictions that should have happened by now
        to_validate = []
        for pred_id, pred in list(self.active_predictions.items()):
            if pred.expected_in_seconds:
                expected_time = pred.predicted_at + timedelta(seconds=pred.expected_in_seconds)
                if now > expected_time:
                    to_validate.append(pred)
        
        for pred in to_validate:
            # Check if predicted event actually occurred
            occurred = await self._check_if_event_occurred(pred)
            
            pred.was_correct = occurred
            pred.outcome_validated_at = now
            pred.actual_outcome = 'occurred' if occurred else 'did_not_occur'
            
            await self._update_prediction_outcome(pred)
            
            # Remove from active
            del self.active_predictions[pred.prediction_id]
            self._prediction_history.append(pred)
            
            if occurred:
                print(f"✅ Prediction validated: {pred.predicted_event}")
            else:
                print(f"❌ Prediction missed: {pred.predicted_event}")
    
    async def _check_if_event_occurred(self, pred: IntentPrediction) -> bool:
        """Check database to see if predicted event actually happened."""
        async with self.db_pool.acquire() as conn:
            # Look for matching telemetry events
            if pred.prediction_type == PredictionType.USER_INTENT:
                row = await conn.fetchrow("""
                    SELECT COUNT(*) as cnt
                    FROM telemetry_events
                    WHERE service = $1
                    AND operation = $2
                    AND timestamp BETWEEN $3 AND $4
                """,
                    pred.predicted_action.get('service'),
                    pred.predicted_action.get('operation'),
                    pred.predicted_at,
                    pred.predicted_at + timedelta(seconds=pred.expected_in_seconds or 60)
                )
                return row and row['cnt'] > 0
        
        return False
    
    async def _persist_prediction(self, pred: IntentPrediction):
        """Persist prediction to database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO predictions 
                (predicted_at, prediction_type, confidence, predicted_event,
                 predicted_action, trigger_features, expected_in_seconds,
                 preparation_action, preparation_params)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                pred.predicted_at,
                pred.prediction_type.value,
                pred.confidence,
                pred.predicted_event,
                json.dumps(pred.predicted_action),
                json.dumps(pred.trigger_features),
                pred.expected_in_seconds,
                pred.preparation_action,
                json.dumps(pred.preparation_params) if pred.preparation_params else None
            )
    
    async def _update_prediction_outcome(self, pred: IntentPrediction):
        """Update prediction with actual outcome."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE predictions 
                SET actual_outcome = $1,
                    outcome_validated_at = $2,
                    was_correct = $3
                WHERE id = $4
            """,
                pred.actual_outcome,
                pred.outcome_validated_at,
                pred.was_correct,
                pred.prediction_id
            )
    
    def get_active_predictions(self) -> List[IntentPrediction]:
        """Get all active predictions."""
        return list(self.active_predictions.values())
    
    def get_predictions_for_service(self, service: str) -> List[IntentPrediction]:
        """Get predictions relevant to a specific service."""
        return [
            p for p in self.active_predictions.values()
            if p.predicted_action.get('service') == service
        ]
    
    def get_prediction_accuracy(self) -> Dict[str, Any]:
        """Calculate prediction accuracy statistics."""
        validated = [p for p in self._prediction_history if p.was_correct is not None]
        
        if not validated:
            return {'accuracy': 0, 'total_validated': 0}
        
        correct = sum(1 for p in validated if p.was_correct)
        
        # By type
        by_type = {}
        for p in validated:
            pt = p.prediction_type.value
            if pt not in by_type:
                by_type[pt] = {'total': 0, 'correct': 0}
            by_type[pt]['total'] += 1
            if p.was_correct:
                by_type[pt]['correct'] += 1
        
        for stats in by_type.values():
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        
        return {
            'accuracy': correct / len(validated),
            'total_validated': len(validated),
            'total_correct': correct,
            'by_type': by_type,
            'active_predictions': len(self.active_predictions),
        }
    
    def get_jit_recommendations(self) -> List[Dict[str, Any]]:
        """Get JIT preparation recommendations."""
        recommendations = []
        
        for pred in self.active_predictions.values():
            should_act, reason = pred.is_actionable()
            if should_act:
                cmd = pred.to_preparation_command()
                if cmd:
                    recommendations.append({
                        'prediction_id': pred.prediction_id,
                        'confidence': pred.confidence,
                        'action': cmd,
                        'reason': reason,
                        'time_sensitive': pred.expected_in_seconds is not None and pred.expected_in_seconds < 300
                    })
        
        # Sort by confidence and urgency
        recommendations.sort(
            key=lambda x: (x['confidence'], x.get('time_sensitive', False)),
            reverse=True
        )
        
        return recommendations[:10]  # Top 10
    
    def stop(self):
        """Stop prediction loops."""
        self._is_running = False
        
        if self._prediction_task:
            self._prediction_task.cancel()
        if self._validation_task:
            self._validation_task.cancel()
        
        print("🛑 Intent Predictor stopped")
    
    def _generate_id(self) -> str:
        """Generate unique ID."""
        import uuid
        return str(uuid.uuid4())[:8]


# Singleton
_predictor: Optional[IntentPredictor] = None


async def get_predictor() -> IntentPredictor:
    """Get or create singleton predictor."""
    global _predictor
    if _predictor is None:
        _predictor = IntentPredictor()
        await _predictor.initialize()
    return _predictor
