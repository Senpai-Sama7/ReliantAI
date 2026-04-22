"""
Metacognitive Autonomy Layer (MAL) for ReliantAI

Enables self-improvement, self-healing, and autonomous learning across
the entire platform.

Usage:
    from integration.metacognitive_layer import MetacognitiveEngine
    
    engine = MetacognitiveEngine()
    await engine.initialize()
    await engine.start_observation_loop()
"""

from .engine import MetacognitiveEngine
from .healing_orchestrator import SelfHealingOrchestrator
from .feedback_collector import FeedbackCollector
from .intent_predictor import IntentPredictor
from .optimizer import AutonomousOptimizer
from .knowledge_consolidator import KnowledgeConsolidator

__version__ = "1.0.0"
__all__ = [
    "MetacognitiveEngine",
    "SelfHealingOrchestrator", 
    "FeedbackCollector",
    "IntentPredictor",
    "AutonomousOptimizer",
    "KnowledgeConsolidator",
]
