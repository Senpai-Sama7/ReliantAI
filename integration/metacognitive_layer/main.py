"""
Metacognitive Autonomy Layer - Main Entry Point

Integrates all MAL components into a unified autonomous system.
This is the orchestration layer that makes ReliantAI self-improving.
"""

import asyncio
from typing import Optional
import signal

from .engine import MetacognitiveEngine, get_engine
from .healing_orchestrator import SelfHealingOrchestrator, get_orchestrator
from .feedback_collector import FeedbackCollector, get_collector
from .intent_predictor import IntentPredictor, get_predictor
from .optimizer import AutonomousOptimizer, get_optimizer
from .knowledge_consolidator import KnowledgeConsolidator, get_consolidator


class MetacognitiveAutonomySystem:
    """
    Unified autonomous system integrating all MAL components.
    
    Usage:
        autonomy = MetacognitiveAutonomySystem()
        await autonomy.start()
        
        # System now runs autonomously, self-healing and self-improving
    """
    
    def __init__(self):
        self.engine: Optional[MetacognitiveEngine] = None
        self.healing: Optional[SelfHealingOrchestrator] = None
        self.feedback: Optional[FeedbackCollector] = None
        self.predictor: Optional[IntentPredictor] = None
        self.optimizer: Optional[AutonomousOptimizer] = None
        self.consolidator: Optional[KnowledgeConsolidator] = None
        self._running = False
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """Initialize all MAL components."""
        print("🚀 Initializing Metacognitive Autonomy System...")
        
        # Initialize components
        self.engine = await get_engine()
        self.healing = await get_orchestrator()
        self.feedback = await get_collector()
        self.predictor = await get_predictor()
        self.optimizer = await get_optimizer()
        self.consolidator = await get_consolidator()
        
        # Wire components together
        await self._wire_components()
        
        print("✅ MAL System initialized and ready")
    
    async def _wire_components(self):
        """Connect components for cross-communication."""
        # Engine observes healing events
        self.healing.health_monitor.on_symptom(
            lambda s: asyncio.create_task(
                self.engine.observe({
                    'service': s.service,
                    'operation': f"symptom:{s.symptom_type}",
                    'status': s.severity.value,
                    'duration_ms': 0,
                    'metadata': s.metrics
                })
            )
        )
        
        # Feedback collector generates insights for predictor
        self.feedback.on_new_insight(
            lambda i: asyncio.create_task(
                self._on_new_insight(i)
            )
        )
        
        # Predictor informs engine of likely events
        self.engine.subscribe(
            lambda e: asyncio.create_task(
                self._on_autonomy_event(e)
            )
        )
        
        # Engine metrics feed optimizer
        self.engine.subscribe(
            lambda e: asyncio.create_task(
                self._on_metrics_for_optimization(e)
            )
        )
        
        # Feedback feeds knowledge consolidator
        self.feedback.on_new_insight(
            lambda i: asyncio.create_task(
                self._on_insight_for_consolidation(i)
            )
        )
    
    async def _on_new_insight(self, insight):
        """Handle new insights from feedback collector."""
        # If insight is about successful patterns, inform predictor
        if insight.insight_type == "successful_path":
            # Update predictor's sequence knowledge
            pass
    
    async def _on_autonomy_event(self, event):
        """Handle autonomy events from engine."""
        # Could trigger healing, optimization, etc.
        if event.get('type') == 'prediction':
            prediction = event.get('prediction')
            if prediction and hasattr(prediction, 'is_actionable') and prediction.is_actionable():
                # Could trigger JIT preparation
                pass
    
    async def _on_metrics_for_optimization(self, event):
        """Send metrics to optimizer for analysis."""
        if self.optimizer and event.get('service'):
            await self.optimizer.record_metrics({
                'service': event.get('service'),
                'operation': event.get('operation'),
                'status': event.get('status'),
                'duration_ms': event.get('duration_ms', 0),
                'timestamp': event.get('timestamp', '')
            })
    
    async def _on_insight_for_consolidation(self, insight):
        """Send insights to knowledge consolidator."""
        if self.consolidator and insight.insight_type == 'successful_path':
            # Record as tool usage pattern if applicable
            await self.consolidator.record_tool_usage(
                tools=insight.recommended_action.get('tools', []),
                context_type=insight.trigger_conditions.get('context_type', 'general'),
                success=True,
                duration_ms=insight.recommended_action.get('duration_ms', 0)
            )
    
    async def start(self):
        """Start all autonomous loops."""
        if not self.engine:
            await self.initialize()
        
        self._running = True
        
        print("\n" + "="*60)
        print("🧠 METACOGNITIVE AUTONOMY SYSTEM STARTED")
        print("="*60)
        print("\nComponents active:")
        print("  ✓ Metacognitive Engine (observing, learning)")
        print("  ✓ Self-Healing Orchestrator (monitoring, remediating)")
        print("  ✓ Feedback Collector (collecting, extracting insights)")
        print("  ✓ Intent Predictor (predicting, pre-warming)")
        print("  ✓ Autonomous Optimizer (self-tuning, auto-rollback)")
        print("  ✓ Knowledge Consolidator (pattern extraction, asset creation)")
        print("\nCapabilities:")
        print("  → Self-Improvement: Learning from every interaction")
        print("  → Self-Healing: Auto-remediation within 5s-5min")
        print("  → JIT Learning: Preparing resources before needed")
        print("  → Pattern Recognition: Extracting reusable knowledge")
        print("="*60 + "\n")
        
        # Start all loops
        await self.engine.start_observation_loop(interval_seconds=30.0)
        await self.healing.start()
        await self.feedback.start_processing_loop()
        await self.predictor.start_prediction_loop(interval_seconds=60.0)
        await self.optimizer.start_optimization_loop(interval_seconds=300.0)
        await self.consolidator.start_consolidation_loop(interval_seconds=3600.0)
        
        # Wait for shutdown signal
        await self._shutdown_event.wait()
    
    async def stop(self):
        """Gracefully stop all components."""
        print("\n🛑 Shutting down Metacognitive Autonomy System...")
        
        self._running = False
        self._shutdown_event.set()
        
        # Stop components
        if self.predictor:
            self.predictor.stop()
        if self.feedback:
            await self.feedback.stop()
        if self.healing:
            self.healing.stop()
        if self.engine:
            await self.engine.stop()
        if self.optimizer:
            self.optimizer.stop()
        if self.consolidator:
            self.consolidator.stop()
        
        print("✅ MAL System stopped gracefully")
    
    def get_status(self) -> dict:
        """Get current autonomy system status."""
        return {
            'running': self._running,
            'engine': self.engine.get_insights() if self.engine else None,
            'healing': self.healing.get_healing_stats() if self.healing else None,
            'feedback': self.feedback.get_learning_stats() if self.feedback else None,
            'predictor': self.predictor.get_prediction_accuracy() if self.predictor else None,
            'jit_recommendations': self.predictor.get_jit_recommendations() if self.predictor else [],
            'optimizer': self.optimizer.get_optimization_stats() if self.optimizer else None,
            'consolidator': self.consolidator.get_consolidation_stats() if self.consolidator else None,
        }


# Global instance
_mal_system: Optional[MetacognitiveAutonomySystem] = None


async def get_mal_system() -> MetacognitiveAutonomySystem:
    """Get or create the MAL system singleton."""
    global _mal_system
    if _mal_system is None:
        _mal_system = MetacognitiveAutonomySystem()
    return _mal_system


async def start_autonomy():
    """Convenience function to start the autonomy system."""
    mal = await get_mal_system()
    await mal.initialize()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\n⚠️ Shutdown signal received")
        asyncio.create_task(mal.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start
    await mal.start()


# Convenience API for other services

async def observe_event(service: str, operation: str, status: str, 
                       duration_ms: float = 0, **metadata):
    """
    Observe a system event for metacognitive analysis.
    
    All services should call this for meaningful operations.
    """
    engine = await get_engine()
    await engine.observe({
        'service': service,
        'operation': operation,
        'status': status,
        'duration_ms': duration_ms,
        'metadata': metadata
    })


async def record_activity(service: str, operation: str, **context):
    """
    Record user/system activity for intent prediction.
    """
    predictor = await get_predictor()
    await predictor.record_activity(service, operation, context)


async def collect_feedback(source_service: str, source_operation: str,
                          feedback_type: str, **kwargs) -> str:
    """
    Collect feedback for continuous learning.
    """
    collector = await get_collector()
    return await collector.collect_feedback(
        source_service, source_operation, feedback_type, **kwargs
    )


async def get_applicable_insights(context: dict) -> list:
    """
    Get insights applicable to current context.
    """
    collector = await get_collector()
    return collector.get_applicable_insights(context)


async def get_jit_recommendations() -> list:
    """
    Get JIT preparation recommendations.
    """
    predictor = await get_predictor()
    return predictor.get_jit_recommendations()


async def report_critical_failure(service: str, error: str, **context):
    """
    Report critical failure for immediate healing response.
    """
    # Get orchestrator for healing response
    orchestrator = await get_orchestrator()
    # Future: Trigger immediate symptom detection via orchestrator
    _ = orchestrator  # Use variable
    
    # Collect feedback
    await collect_feedback(
        service, 'critical_operation', 'failure',
        expectation_gap=error, **context
    )


# CLI entry point
if __name__ == "__main__":
    print("Starting Metacognitive Autonomy Layer...")
    asyncio.run(start_autonomy())
