"""
FastAPI endpoints for Metacognitive Autonomy Layer.

Provides health checks, metrics, and status endpoints for monitoring
the self-improving system.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

from .main import get_mal_system, MetacognitiveAutonomySystem


# Prometheus metrics support (optional)
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


app = FastAPI(
    title="Metacognitive Autonomy Layer API",
    description="API for monitoring and managing the self-improving system",
    version="1.0.0"
)

# Prometheus metrics (if available)
if PROMETHEUS_AVAILABLE:
    # Metacognitive metrics
    observations_total = Counter(
        'mal_observations_total',
        'Total observations processed',
        ['service', 'status']
    )
    
    patterns_learned = Gauge(
        'mal_patterns_learned',
        'Number of learned patterns'
    )
    
    predictions_active = Gauge(
        'mal_predictions_active',
        'Number of active predictions'
    )
    
    # Healing metrics
    healing_events_total = Counter(
        'mal_healing_events_total',
        'Total healing events',
        ['service', 'outcome']
    )
    
    healing_duration_seconds = Histogram(
        'mal_healing_duration_seconds',
        'Time to heal',
        ['service', 'action_type']
    )
    
    # Optimization metrics
    optimizations_applied = Counter(
        'mal_optimizations_applied_total',
        'Optimizations applied',
        ['domain']
    )
    
    optimizations_rolled_back = Counter(
        'mal_optimizations_rolled_back_total',
        'Optimizations rolled back',
        ['domain']
    )
    
    # Consolidation metrics
    knowledge_extracted = Counter(
        'mal_knowledge_extracted_total',
        'Knowledge patterns extracted',
        ['pattern_type']
    )


async def get_system() -> MetacognitiveAutonomySystem:
    """Dependency to get the MAL system."""
    return await get_mal_system()


@app.get("/health")
async def health_check(system: MetacognitiveAutonomySystem = Depends(get_system)):
    """
    Health check endpoint for MAL.
    
    Returns:
        - status: "healthy" or "degraded"
        - components: Status of each component
        - uptime: System uptime if running
    """
    status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'components': {}
    }
    
    # Check each component
    if system.engine:
        engine_insights = system.engine.get_insights()
        status['components']['engine'] = {
            'status': 'healthy' if engine_insights.get('status') == 'active' else 'degraded',
            'patterns': engine_insights.get('patterns_learned', 0),
            'predictions': engine_insights.get('active_predictions', 0)
        }
    else:
        status['components']['engine'] = {'status': 'unknown'}
    
    if system.healing:
        healing_stats = system.healing.get_healing_stats()
        status['components']['healing'] = {
            'status': 'healthy',
            'events_24h': healing_stats.get('healing_events_24h', 0),
            'success_rate': healing_stats.get('success_rate', 0)
        }
    else:
        status['components']['healing'] = {'status': 'unknown'}
    
    if system.feedback:
        feedback_stats = system.feedback.get_learning_stats()
        status['components']['feedback'] = {
            'status': 'healthy',
            'insights': feedback_stats.get('active_insights', 0),
            'buffer_size': feedback_stats.get('feedback_buffer_size', 0)
        }
    else:
        status['components']['feedback'] = {'status': 'unknown'}
    
    if system.predictor:
        accuracy = system.predictor.get_prediction_accuracy()
        status['components']['predictor'] = {
            'status': 'healthy',
            'accuracy': accuracy.get('overall_accuracy', 0) if accuracy else 0
        }
    else:
        status['components']['predictor'] = {'status': 'unknown'}
    
    if system.optimizer:
        opt_stats = system.optimizer.get_optimization_stats()
        status['components']['optimizer'] = {
            'status': 'healthy',
            'optimizations': opt_stats.get('total_optimizations', 0),
            'testing': opt_stats.get('currently_testing', 0)
        }
    else:
        status['components']['optimizer'] = {'status': 'unknown'}
    
    if system.consolidator:
        cons_stats = system.consolidator.get_consolidation_stats()
        status['components']['consolidator'] = {
            'status': 'healthy',
            'patterns': cons_stats.get('consolidated_patterns', 0)
        }
    else:
        status['components']['consolidator'] = {'status': 'unknown'}
    
    # Overall status
    component_statuses = [c['status'] for c in status['components'].values()]
    if any(s == 'degraded' for s in component_statuses):
        status['status'] = 'degraded'
    if any(s == 'unknown' for s in component_statuses):
        status['status'] = 'initializing'
    
    return status


@app.get("/status")
async def full_status(system: MetacognitiveAutonomySystem = Depends(get_system)):
    """
    Full system status with all component details.
    
    Returns comprehensive status from all MAL components.
    """
    return system.get_status()


@app.get("/metrics")
async def metrics_endpoint(system: MetacognitiveAutonomySystem = Depends(get_system)):
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format if prometheus_client is installed.
    """
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Prometheus client not installed. Run: pip install prometheus-client"
        )
    
    # Update gauges from current state
    if system.engine:
        insights = system.engine.get_insights()
        patterns_learned.set(insights.get('patterns_learned', 0))
        predictions_active.set(insights.get('active_predictions', 0))
    
    # Generate metrics
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/insights")
async def get_insights(
    component: Optional[str] = None,
    system: MetacognitiveAutonomySystem = Depends(get_system)
):
    """
    Get metacognitive insights.
    
    Args:
        component: Optional component filter ('engine', 'healing', 'feedback', etc.)
    
    Returns:
        Insights from the specified component or all components.
    """
    insights = {}
    
    if component is None or component == 'engine':
        if system.engine:
            insights['engine'] = system.engine.get_insights()
    
    if component is None or component == 'healing':
        if system.healing:
            insights['healing'] = system.healing.get_healing_stats()
    
    if component is None or component == 'feedback':
        if system.feedback:
            insights['feedback'] = system.feedback.get_learning_stats()
    
    if component is None or component == 'predictor':
        if system.predictor:
            insights['predictor'] = system.predictor.get_prediction_accuracy()
    
    if component is None or component == 'optimizer':
        if system.optimizer:
            insights['optimizer'] = system.optimizer.get_optimization_stats()
    
    if component is None or component == 'consolidator':
        if system.consolidator:
            insights['consolidator'] = system.consolidator.get_consolidation_stats()
    
    return insights


@app.get("/predictions")
async def get_predictions(system: MetacognitiveAutonomySystem = Depends(get_system)):
    """
    Get active predictions.
    
    Returns:
        List of active predictions with confidence scores.
    """
    if not system.predictor:
        return {'predictions': [], 'error': 'Predictor not initialized'}
    
    predictions = system.predictor.get_active_predictions()
    
    return {
        'predictions': [
            {
                'id': p.prediction_id,
                'type': p.prediction_type,
                'confidence': p.confidence,
                'predicted_at': p.predicted_at.isoformat(),
                'actionable': p.is_actionable() if hasattr(p, 'is_actionable') else False,
                'preparation': p.preparation_action
            }
            for p in predictions
        ],
        'count': len(predictions)
    }


@app.get("/knowledge")
async def get_knowledge(
    context: Optional[str] = None,
    system: MetacognitiveAutonomySystem = Depends(get_system)
):
    """
    Get applicable knowledge for context.
    
    Args:
        context: Optional context filter (JSON string)
    
    Returns:
        Knowledge applicable to the context.
    """
    if not system.consolidator:
        return {'knowledge': [], 'error': 'Consolidator not initialized'}
    
    context_dict = {}
    if context:
        import json
        try:
            context_dict = json.loads(context)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid context JSON")
    
    knowledge = system.consolidator.get_applicable_knowledge(context_dict)
    
    return {
        'knowledge': [
            {
                'id': k.knowledge_id,
                'type': k.pattern_type.value,
                'confidence': k.confidence_score,
                'artifact_type': k.artifact_type,
                'usage_count': k.usage_count
            }
            for k in knowledge
        ],
        'count': len(knowledge)
    }


@app.post("/observe")
async def observe_event(
    event: Dict[str, Any],
    system: MetacognitiveAutonomySystem = Depends(get_system)
):
    """
    Manually submit an observation for analysis.
    
    This endpoint allows external services to feed events into the
    metacognitive system.
    
    Args:
        event: Event data with service, operation, status, etc.
    
    Returns:
        Confirmation that observation was received.
    """
    if not system.engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    required = ['service', 'operation', 'status']
    if not all(k in event for k in required):
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {required}"
        )
    
    await system.engine.observe(event)
    
    # Update Prometheus counter if available
    if PROMETHEUS_AVAILABLE:
        observations_total.labels(
            service=event.get('service', 'unknown'),
            status=event.get('status', 'unknown')
        ).inc()
    
    return {
        'status': 'observed',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@app.post("/feedback")
async def submit_feedback(
    service: str,
    operation: str,
    feedback_type: str,
    details: Optional[Dict[str, Any]] = None,
    system: MetacognitiveAutonomySystem = Depends(get_system)
):
    """
    Submit feedback for learning.
    
    Args:
        service: Service name
        operation: Operation name
        feedback_type: Type of feedback (success, failure, user_correction, etc.)
        details: Additional feedback details
    
    Returns:
        Feedback ID for reference.
    """
    if not system.feedback:
        raise HTTPException(status_code=503, detail="Feedback collector not initialized")
    
    details = details or {}
    
    feedback_id = await system.feedback.collect_feedback(
        source_service=service,
        source_operation=operation,
        feedback_type=feedback_type,
        **details
    )
    
    return {
        'feedback_id': feedback_id,
        'status': 'recorded',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        'name': 'Metacognitive Autonomy Layer API',
        'version': '1.0.0',
        'endpoints': [
            '/health - Health check',
            '/status - Full system status',
            '/metrics - Prometheus metrics',
            '/insights - Component insights',
            '/predictions - Active predictions',
            '/knowledge - Applicable knowledge',
            '/observe - Submit observation',
            '/feedback - Submit feedback'
        ]
    }


# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize MAL system on startup."""
    print("🚀 Starting Metacognitive Autonomy Layer API...")
    system = await get_mal_system()
    await system.initialize()
    print("✅ MAL API ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown MAL system."""
    print("\n🛑 Shutting down MAL API...")
    system = await get_mal_system()
    await system.stop()
    print("✅ MAL API stopped")
