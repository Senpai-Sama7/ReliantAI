"""
Intelligent Routing Module - Cross-System Orchestrator with MAL Predictions

Integrates Metacognitive Autonomy Layer predictions for optimal task routing.
Uses learned patterns to route tasks to the most appropriate system.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

# Import MAL components
from metacognitive_layer.main import MetacognitiveAutonomySystem
from metacognitive_layer.predictor import IntentPredictor, get_predictor
from metacognitive_layer.optimizer import AutonomousOptimizer, get_optimizer

# Import orchestrator
from cross_system_orchestrator import CrossSystemOrchestrator, SystemType


class RoutingStrategy(str, Enum):
    """Available routing strategies."""
    FASTEST = "fastest"  # Minimize latency
    MOST_CAPABLE = "most_capable"  # Best match for capability
    COST_OPTIMIZED = "cost_optimized"  # Minimize cost
    MAL_PREDICTED = "mal_predicted"  # Use MAL predictions
    FALLBACK_SAFE = "fallback_safe"  # Prioritize systems with good fallback


@dataclass
class RoutingDecision:
    """A routing decision with MAL insights."""
    target_system: SystemType
    confidence: float  # MAL prediction confidence (0-1)
    strategy: RoutingStrategy
    estimated_latency_ms: float
    estimated_success_rate: float
    reasoning: str
    fallback_system: Optional[SystemType] = None
    metadata: Dict[str, Any] = None


@dataclass
class TaskProfile:
    """Profile of a task for routing analysis."""
    task_id: str
    task_type: str
    required_capabilities: List[str]
    payload_size: int
    priority: str  # "low", "medium", "high", "critical"
    deadline_ms: Optional[int] = None
    historical_patterns: Dict[str, Any] = None


class IntelligentRouter:
    """
    Routes tasks across systems using MAL predictions and learned patterns.
    
    Features:
    - MAL intent prediction for task classification
    - Autonomous optimization for routing decisions
    - Historical pattern analysis
    - Dynamic fallback selection
    - Performance-based routing adjustments
    """
    
    def __init__(
        self,
        orchestrator: CrossSystemOrchestrator,
        mal_system: Optional[MetacognitiveAutonomySystem] = None,
        default_strategy: RoutingStrategy = RoutingStrategy.MAL_PREDICTED
    ):
        self.orchestrator = orchestrator
        self.mal = mal_system
        self.default_strategy = default_strategy
        
        # MAL components (lazy-loaded)
        self._predictor: Optional[IntentPredictor] = None
        self._optimizer: Optional[AutonomousOptimizer] = None
        
        # Routing history for learning
        self._routing_history: List[Dict[str, Any]] = []
        self._system_performance: Dict[SystemType, Dict[str, float]] = {}
        
        # Capability mappings
        self._capability_systems = self._build_capability_map()
        
        # Callbacks for routing events
        self._on_routing_decision: List[Callable[[RoutingDecision], None]] = []
    
    async def _get_predictor(self) -> Optional[IntentPredictor]:
        """Lazy-load MAL predictor."""
        if self._predictor is None and self.mal:
            self._predictor = await get_predictor()
        return self._predictor
    
    async def _get_optimizer(self) -> Optional[AutonomousOptimizer]:
        """Lazy-load MAL optimizer."""
        if self._optimizer is None and self.mal:
            self._optimizer = await get_optimizer()
        return self._optimizer
    
    def _build_capability_map(self) -> Dict[str, List[SystemType]]:
        """Build mapping of capabilities to systems."""
        return {
            "workflow": [SystemType.APEX, SystemType.ACROPOLIS],
            "uncertainty-calibration": [SystemType.APEX],
            "skill-execution": [SystemType.APEX, SystemType.CITADEL],
            "hvac-dispatch": [SystemType.MONEY],
            "sms-integration": [SystemType.MONEY],
            "chat-completion": [SystemType.CITADEL],
            "nl-agent": [SystemType.CITADEL],
            "memory-system": [SystemType.ACROPOLIS],
            "polyglot-agents": [SystemType.ACROPOLIS],
        }
    
    async def route_task(
        self,
        task_profile: TaskProfile,
        strategy: Optional[RoutingStrategy] = None
    ) -> RoutingDecision:
        """
        Route a task to the optimal system using MAL predictions.
        
        Args:
            task_profile: Description of the task to route
            strategy: Routing strategy (defaults to MAL_PREDICTED)
        
        Returns:
            RoutingDecision with target system and confidence
        """
        strategy = strategy or self.default_strategy
        
        # Get candidate systems based on capabilities
        candidates = self._get_candidate_systems(task_profile.required_capabilities)
        
        if not candidates:
            # No system has required capabilities - use APEX as default
            return RoutingDecision(
                target_system=SystemType.APEX,
                confidence=0.5,
                strategy=strategy,
                estimated_latency_ms=1000,
                estimated_success_rate=0.6,
                reasoning="No exact capability match, routing to APEX as orchestrator"
            )
        
        # Apply routing strategy
        if strategy == RoutingStrategy.MAL_PREDICTED:
            return await self._route_mal_predicted(task_profile, candidates)
        elif strategy == RoutingStrategy.FASTEST:
            return self._route_fastest(task_profile, candidates)
        elif strategy == RoutingStrategy.MOST_CAPABLE:
            return self._route_most_capable(task_profile, candidates)
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._route_cost_optimized(task_profile, candidates)
        elif strategy == RoutingStrategy.FALLBACK_SAFE:
            return self._route_fallback_safe(task_profile, candidates)
        else:
            return await self._route_mal_predicted(task_profile, candidates)
    
    async def _route_mal_predicted(
        self,
        task_profile: TaskProfile,
        candidates: List[SystemType]
    ) -> RoutingDecision:
        """Route using MAL intent prediction and optimization."""
        predictor = await self._get_predictor()
        optimizer = await self._get_optimizer()
        
        if not predictor or not optimizer:
            # MAL unavailable - fall back to heuristic routing
            return self._route_heuristic(task_profile, candidates)
        
        # Use MAL to predict task characteristics
        prediction = await predictor.predict_next_intent(
            task_profile.task_type,
            task_profile.historical_patterns or {}
        )
        
        # Get current system health from orchestrator
        system_health = self.orchestrator.get_all_system_status()
        
        # Score each candidate system
        best_system = None
        best_score = -1
        best_reasoning = ""
        
        for system in candidates:
            score = 0.0
            reasoning_parts = []
            
            # Health score (0-30)
            health = system_health.get(system)
            if health:
                if health.status == "healthy":
                    score += 30
                    reasoning_parts.append(f"{system.value} is healthy")
                elif health.status == "degraded":
                    score += 15
                    reasoning_parts.append(f"{system.value} is degraded")
            
            # Capability match score (0-40)
            capabilities = self.orchestrator._get_system_capabilities(system)
            matches = len(set(task_profile.required_capabilities) & set(capabilities))
            capability_score = (matches / len(task_profile.required_capabilities)) * 40
            score += capability_score
            reasoning_parts.append(f"capability match: {matches}/{len(task_profile.required_capabilities)}")
            
            # Historical performance score (0-30)
            perf = self._system_performance.get(system, {})
            success_rate = perf.get('success_rate', 0.8)
            score += success_rate * 30
            reasoning_parts.append(f"historical success: {success_rate:.1%}")
            
            if score > best_score:
                best_score = score
                best_system = system
                best_reasoning = "; ".join(reasoning_parts)
        
        # Calculate confidence based on score quality
        confidence = min(best_score / 100, 0.95)
        
        # Determine fallback
        fallback = self._select_fallback(best_system, candidates, system_health)
        
        decision = RoutingDecision(
            target_system=best_system or SystemType.APEX,
            confidence=confidence,
            strategy=RoutingStrategy.MAL_PREDICTED,
            estimated_latency_ms=self._estimate_latency(best_system),
            estimated_success_rate=best_score / 100,
            reasoning=f"MAL routing: {best_reasoning}",
            fallback_system=fallback,
            metadata={
                "prediction": prediction,
                "mal_enabled": True
            }
        )
        
        # Record for learning
        self._record_routing_decision(task_profile, decision)
        
        return decision
    
    def _route_heuristic(
        self,
        task_profile: TaskProfile,
        candidates: List[SystemType]
    ) -> RoutingDecision:
        """Heuristic routing when MAL is unavailable."""
        # Simple: pick first healthy candidate
        system_health = self.orchestrator.get_all_system_status()
        
        for system in candidates:
            health = system_health.get(system)
            if health and health.status == "healthy":
                return RoutingDecision(
                    target_system=system,
                    confidence=0.6,
                    strategy=RoutingStrategy.FASTEST,
                    estimated_latency_ms=self._estimate_latency(system),
                    estimated_success_rate=0.75,
                    reasoning="Heuristic: first healthy system with matching capabilities"
                )
        
        # All degraded - use first candidate anyway
        return RoutingDecision(
            target_system=candidates[0],
            confidence=0.4,
            strategy=RoutingStrategy.FASTEST,
            estimated_latency_ms=self._estimate_latency(candidates[0]),
            estimated_success_rate=0.5,
            reasoning="Heuristic: all systems degraded, using first available"
        )
    
    def _route_fastest(
        self,
        task_profile: TaskProfile,
        candidates: List[SystemType]
    ) -> RoutingDecision:
        """Route to system with lowest estimated latency."""
        best_system = min(candidates, key=lambda s: self._estimate_latency(s))
        
        return RoutingDecision(
            target_system=best_system,
            confidence=0.7,
            strategy=RoutingStrategy.FASTEST,
            estimated_latency_ms=self._estimate_latency(best_system),
            estimated_success_rate=0.75,
            reasoning="Strategy: minimize latency"
        )
    
    def _route_most_capable(
        self,
        task_profile: TaskProfile,
        candidates: List[SystemType]
    ) -> RoutingDecision:
        """Route to system with best capability match."""
        best_system = None
        best_match = 0
        
        for system in candidates:
            capabilities = self.orchestrator._get_system_capabilities(system)
            matches = len(set(task_profile.required_capabilities) & set(capabilities))
            if matches > best_match:
                best_match = matches
                best_system = system
        
        return RoutingDecision(
            target_system=best_system or candidates[0],
            confidence=0.75,
            strategy=RoutingStrategy.MOST_CAPABLE,
            estimated_latency_ms=self._estimate_latency(best_system or candidates[0]),
            estimated_success_rate=0.8,
            reasoning=f"Strategy: best capability match ({best_match}/{len(task_profile.required_capabilities)})"
        )
    
    def _route_cost_optimized(
        self,
        task_profile: TaskProfile,
        candidates: List[SystemType]
    ) -> RoutingDecision:
        """Route to minimize cost (prefer Citadel over APEX for simple tasks)."""
        # Cost ranking: Citadel < Acropolis < Money < APEX
        cost_rank = {
            SystemType.CITADEL: 1,
            SystemType.ACROPOLIS: 2,
            SystemType.MONEY: 3,
            SystemType.APEX: 4
        }
        
        # Sort by cost, pick lowest with matching capabilities
        sorted_candidates = sorted(candidates, key=lambda s: cost_rank.get(s, 99))
        
        return RoutingDecision(
            target_system=sorted_candidates[0],
            confidence=0.65,
            strategy=RoutingStrategy.COST_OPTIMIZED,
            estimated_latency_ms=self._estimate_latency(sorted_candidates[0]),
            estimated_success_rate=0.7,
            reasoning="Strategy: minimize operational cost"
        )
    
    def _route_fallback_safe(
        self,
        task_profile: TaskProfile,
        candidates: List[SystemType]
    ) -> RoutingDecision:
        """Route prioritizing systems with good fallback mechanisms."""
        # Ranking by fallback quality
        fallback_rank = {
            SystemType.MONEY: 1,  # Has local triage fallback
            SystemType.APEX: 2,   # Has uncertainty gating + HITL
            SystemType.CITADEL: 3,
            SystemType.ACROPOLIS: 4
        }
        
        sorted_candidates = sorted(candidates, key=lambda s: fallback_rank.get(s, 99))
        
        return RoutingDecision(
            target_system=sorted_candidates[0],
            confidence=0.7,
            strategy=RoutingStrategy.FALLBACK_SAFE,
            estimated_latency_ms=self._estimate_latency(sorted_candidates[0]),
            estimated_success_rate=0.75,
            reasoning="Strategy: prioritize fallback mechanisms"
        )
    
    def _get_candidate_systems(self, capabilities: List[str]) -> List[SystemType]:
        """Get systems that have the required capabilities."""
        candidates = set()
        for cap in capabilities:
            systems = self._capability_systems.get(cap, [])
            candidates.update(systems)
        
        return list(candidates)
    
    def _estimate_latency(self, system: Optional[SystemType]) -> float:
        """Estimate latency for a system (ms)."""
        base_latencies = {
            SystemType.APEX: 500,      # 4-layer pipeline
            SystemType.MONEY: 300,     # CrewAI workflow
            SystemType.CITADEL: 200,   # NL agent
            SystemType.ACROPOLIS: 150  # Rust-based
        }
        
        if not system:
            return 1000
        
        # Add health-based adjustment
        health = self.orchestrator.get_system_status(system)
        if health and health.status == "degraded":
            return base_latencies.get(system, 500) * 2
        
        return base_latencies.get(system, 500)
    
    def _select_fallback(
        self,
        primary: SystemType,
        candidates: List[SystemType],
        health: Dict[SystemType, Any]
    ) -> Optional[SystemType]:
        """Select a fallback system if primary fails."""
        for system in candidates:
            if system != primary:
                health_info = health.get(system)
                if health_info and health_info.status == "healthy":
                    return system
        return None
    
    def _record_routing_decision(
        self,
        task: TaskProfile,
        decision: RoutingDecision
    ):
        """Record routing decision for learning."""
        self._routing_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": task.task_id,
            "task_type": task.task_type,
            "decision": decision,
            "outcome": None  # To be updated after execution
        })
        
        # Notify callbacks
        for callback in self._on_routing_decision:
            callback(decision)
    
    def record_outcome(
        self,
        task_id: str,
        success: bool,
        latency_ms: float,
        error: Optional[str] = None
    ):
        """Record the outcome of a routing decision for learning."""
        for record in reversed(self._routing_history):
            if record["task_id"] == task_id:
                record["outcome"] = {
                    "success": success,
                    "latency_ms": latency_ms,
                    "error": error
                }
                
                # Update system performance stats
                decision = record["decision"]
                system = decision.target_system
                
                if system not in self._system_performance:
                    self._system_performance[system] = {
                        "total_requests": 0,
                        "successful_requests": 0,
                        "total_latency_ms": 0,
                        "success_rate": 0.8
                    }
                
                perf = self._system_performance[system]
                perf["total_requests"] += 1
                if success:
                    perf["successful_requests"] += 1
                perf["total_latency_ms"] += latency_ms
                perf["success_rate"] = perf["successful_requests"] / perf["total_requests"]
                
                break
    
    def on_routing_decision(self, callback: Callable[[RoutingDecision], None]):
        """Register callback for routing decisions."""
        self._on_routing_decision.append(callback)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        total = len(self._routing_history)
        with_outcomes = len([r for r in self._routing_history if r.get("outcome")])
        successful = len([r for r in self._routing_history 
                        if r.get("outcome", {}).get("success")])
        
        return {
            "total_routings": total,
            "completed_with_outcome": with_outcomes,
            "successful": successful,
            "success_rate": successful / with_outcomes if with_outcomes > 0 else 0,
            "system_performance": self._system_performance,
            "strategies_used": self._count_strategies()
        }
    
    def _count_strategies(self) -> Dict[str, int]:
        """Count usage of each routing strategy."""
        counts = {}
        for record in self._routing_history:
            strategy = record["decision"].strategy.value
            counts[strategy] = counts.get(strategy, 0) + 1
        return counts
