"""
HITL (Human-in-the-Loop) Optimizer

Reduces bottlenecks in human review processes through:
1. Intelligent batching of similar decisions
2. Priority queuing with escalation
3. Auto-approval for low-risk patterns
4. Predictive pre-fetching of context
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from collections import defaultdict
import heapq
import asyncio


class HITLDecisionType(str, Enum):
    """Types of decisions requiring human review."""
    LOW_CONFIDENCE = "low_confidence"  # AI confidence < 0.65
    HIGH_STAKES = "high_stakes"        # High business impact
    NOVEL_DOMAIN = "novel_domain"        # Unfamiliar domain
    DISPUTED = "disputed"              # Layer 4 flagged quality issues
    SAFETY_CHECK = "safety_check"      # Life-safety related
    COMPLIANCE = "compliance"          # Regulatory requirement


class HITLPriority(int, Enum):
    """Priority levels for HITL queue."""
    CRITICAL = 1   # Safety, compliance violations
    HIGH = 2       # Revenue-impacting, time-sensitive
    MEDIUM = 3     # Standard review
    LOW = 4        # Training, low stakes


@dataclass
class HITLRequest:
    """A request for human review."""
    request_id: str
    decision_type: HITLDecisionType
    priority: HITLPriority
    
    # AI context
    ai_confidence: float
    ai_recommendation: str
    uncertainty_aleatoric: float
    uncertainty_epistemic: float
    
    # Business context
    stakes: str  # "low", "medium", "high"
    domain_novelty: float
    estimated_value: float  # Business value at stake
    deadline: Optional[datetime] = None
    
    # Content
    context_summary: str
    full_context: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    system_origin: str = "unknown"  # APEX, Money, etc.
    correlation_id: str = ""
    
    # Batch grouping
    batch_key: Optional[str] = None  # For similar request batching
    
    def __lt__(self, other):
        """Compare for priority queue (lower priority number = higher priority)."""
        if not isinstance(other, HITLRequest):
            return NotImplemented
        return self.priority.value < other.priority.value


@dataclass
class HITLDecision:
    """A human decision on a HITL request."""
    request_id: str
    approved: bool
    decision: str  # "approve", "reject", "modify", "escalate"
    human_notes: str
    modifications: Dict[str, Any] = field(default_factory=dict)
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    reviewer_id: str = "anonymous"


@dataclass
class AutoApprovalRule:
    """Rule for automatic approval of low-risk decisions."""
    name: str
    decision_types: Set[HITLDecisionType]
    min_confidence: float
    max_uncertainty: float
    max_stakes: str  # "low" or "medium"
    max_domain_novelty: float
    cooldown_hours: int = 24  # Time before same pattern needs review again


class HITLOptimizer:
    """
    Optimizes human-in-the-loop processes.
    
    Features:
    - Priority-based queuing with escalation
    - Batching of similar decisions for bulk review
    - Auto-approval for trusted patterns
    - Predictive context pre-fetching
    - Reviewer load balancing
    """
    
    def __init__(
        self,
        max_queue_size: int = 1000,
        auto_approval_enabled: bool = True,
        batching_enabled: bool = True,
        batch_window_seconds: float = 300.0,  # 5 minutes
    ):
        self.max_queue_size = max_queue_size
        self.auto_approval_enabled = auto_approval_enabled
        self.batching_enabled = batching_enabled
        self.batch_window_seconds = batch_window_seconds
        
        # Priority queue (min-heap by priority)
        self._queue: List[HITLRequest] = []
        self._queue_lock = asyncio.Lock()
        
        # Tracking
        self._requests: Dict[str, HITLRequest] = {}
        self._decisions: Dict[str, HITLDecision] = {}
        self._pending_batches: Dict[str, List[HITLRequest]] = defaultdict(list)
        
        # Auto-approval rules
        self._auto_approval_rules: List[AutoApprovalRule] = []
        self._init_default_rules()
        
        # Pattern tracking for auto-approval
        self._approval_patterns: Dict[str, datetime] = {}  # pattern_key -> last_approval
        
        # Statistics
        self._stats = {
            "submitted": 0,
            "auto_approved": 0,
            "human_reviewed": 0,
            "batched": 0,
            "avg_decision_time_ms": 0,
        }
        
        # Callbacks
        self._on_auto_approve: List[Callable[[HITLRequest], None]] = []
        self._on_human_required: List[Callable[[HITLRequest], None]] = []
        self._on_batch_ready: List[Callable[[str, List[HITLRequest]], None]] = []
    
    def _init_default_rules(self):
        """Initialize default auto-approval rules."""
        self._auto_approval_rules = [
            AutoApprovalRule(
                name="trusted_low_confidence",
                decision_types={HITLDecisionType.LOW_CONFIDENCE},
                min_confidence=0.60,
                max_uncertainty=0.25,
                max_stakes="low",
                max_domain_novelty=0.7,
            ),
            AutoApprovalRule(
                name="routine_disputed",
                decision_types={HITLDecisionType.DISPUTED},
                min_confidence=0.70,
                max_uncertainty=0.20,
                max_stakes="medium",
                max_domain_novelty=0.5,
            ),
        ]
    
    async def submit_request(self, request: HITLRequest) -> Dict[str, Any]:
        """
        Submit a request for human review.
        
        Returns:
            Dict with 'action' ('auto_approved', 'queued', or 'batched')
        """
        self._stats["submitted"] += 1
        
        # Check auto-approval
        if self.auto_approval_enabled:
            auto_approve_result = self._check_auto_approval(request)
            if auto_approve_result:
                self._stats["auto_approved"] += 1
                
                # Record pattern
                pattern_key = self._get_pattern_key(request)
                self._approval_patterns[pattern_key] = datetime.now(UTC)
                
                # Notify callbacks
                for callback in self._on_auto_approve:
                    callback(request)
                
                return {
                    "action": "auto_approved",
                    "request_id": request.request_id,
                    "rule": auto_approve_result,
                    "decision": "approve"
                }
        
        # Try batching if enabled
        if self.batching_enabled and request.batch_key:
            batch = self._pending_batches[request.batch_key]
            batch.append(request)
            
            # Check if batch is ready
            if len(batch) >= 5:  # Batch threshold
                self._stats["batched"] += 1
                for callback in self._on_batch_ready:
                    callback(request.batch_key, batch.copy())
                self._pending_batches[request.batch_key] = []
                
                return {
                    "action": "batched",
                    "request_id": request.request_id,
                    "batch_key": request.batch_key,
                    "batch_size": len(batch)
                }
        
        # Add to priority queue
        async with self._queue_lock:
            if len(self._queue) >= self.max_queue_size:
                # Queue full - reject or escalate
                return {
                    "action": "rejected",
                    "reason": "queue_full",
                    "request_id": request.request_id
                }
            
            heapq.heappush(self._queue, request)
            self._requests[request.request_id] = request
        
        # Notify callbacks
        for callback in self._on_human_required:
            callback(request)
        
        return {
            "action": "queued",
            "request_id": request.request_id,
            "position": self._get_queue_position(request.request_id),
            "estimated_wait_seconds": self._estimate_wait_time(request)
        }
    
    def _check_auto_approval(self, request: HITLRequest) -> Optional[str]:
        """Check if request qualifies for auto-approval."""
        for rule in self._auto_approval_rules:
            # Check decision type
            if request.decision_type not in rule.decision_types:
                continue
            
            # Check confidence
            if request.ai_confidence < rule.min_confidence:
                continue
            
            # Check uncertainty
            total_uncertainty = request.uncertainty_aleatoric + request.uncertainty_epistemic
            if total_uncertainty > rule.max_uncertainty:
                continue
            
            # Check stakes
            stakes_priority = {"low": 1, "medium": 2, "high": 3}
            if stakes_priority.get(request.stakes, 3) > stakes_priority.get(rule.max_stakes, 3):
                continue
            
            # Check domain novelty
            if request.domain_novelty > rule.max_domain_novelty:
                continue
            
            # Check cooldown
            pattern_key = self._get_pattern_key(request)
            last_approval = self._approval_patterns.get(pattern_key)
            if last_approval:
                cooldown_expiry = last_approval + timedelta(hours=rule.cooldown_hours)
                if datetime.now(UTC) < cooldown_expiry:
                    continue
            
            return rule.name
        
        return None
    
    def _get_pattern_key(self, request: HITLRequest) -> str:
        """Generate a pattern key for tracking similar requests."""
        return f"{request.decision_type.value}:{request.system_origin}:{request.stakes}"
    
    def _get_queue_position(self, request_id: str) -> int:
        """Get approximate position in queue."""
        for i, req in enumerate(self._queue):
            if req.request_id == request_id:
                return i + 1
        return -1
    
    def _estimate_wait_time(self, request: HITLRequest) -> float:
        """Estimate wait time in seconds based on queue position and priority."""
        position = self._get_queue_position(request.request_id)
        if position < 0:
            return 0
        
        # Higher priority = faster service
        priority_factor = request.priority.value
        base_time_per_item = 60  # seconds
        
        return position * base_time_per_item / priority_factor
    
    async def get_next_request(
        self,
        reviewer_capabilities: Optional[List[str]] = None,
        max_batch_size: int = 1
    ) -> Optional[HITLRequest]:
        """
        Get the next request for human review.
        
        Args:
            reviewer_capabilities: Optional list of reviewer capabilities
            max_batch_size: Number of requests to return (for batch review)
        
        Returns:
            Next HITLRequest or None if queue empty
        """
        async with self._queue_lock:
            if not self._queue:
                return None
            
            # Get highest priority item
            request = heapq.heappop(self._queue)
            
            # Check if reviewer can handle this type
            if reviewer_capabilities:
                required_caps = self._get_required_capabilities(request)
                if not any(cap in reviewer_capabilities for cap in required_caps):
                    # Put back and try next
                    heapq.heappush(self._queue, request)
                    return None
            
            return request
    
    def _get_required_capabilities(self, request: HITLRequest) -> List[str]:
        """Get capabilities required to review this request."""
        capability_map = {
            HITLDecisionType.LOW_CONFIDENCE: ["ai_review"],
            HITLDecisionType.HIGH_STAKES: ["business_judgment"],
            HITLDecisionType.NOVEL_DOMAIN: ["domain_expert"],
            HITLDecisionType.DISPUTED: ["quality_review"],
            HITLDecisionType.SAFETY_CHECK: ["safety_officer"],
            HITLDecisionType.COMPLIANCE: ["compliance_officer"],
        }
        return capability_map.get(request.decision_type, ["general"])
    
    async def submit_decision(self, decision: HITLDecision) -> bool:
        """Submit a human decision."""
        if decision.request_id not in self._requests:
            return False
        
        self._decisions[decision.request_id] = decision
        self._stats["human_reviewed"] += 1
        
        # Calculate decision time
        request = self._requests[decision.request_id]
        decision_time = (decision.decided_at - request.created_at).total_seconds() * 1000
        
        # Update running average
        n = self._stats["human_reviewed"]
        old_avg = self._stats["avg_decision_time_ms"]
        self._stats["avg_decision_time_ms"] = (old_avg * (n - 1) + decision_time) / n
        
        return True
    
    def get_batch_for_review(
        self,
        batch_key: str,
        max_size: int = 10
    ) -> List[HITLRequest]:
        """Get pending requests in a batch for bulk review."""
        batch = self._pending_batches.get(batch_key, [])
        return batch[:max_size]
    
    def flush_batch(self, batch_key: str) -> List[HITLRequest]:
        """Flush a batch and return all pending requests."""
        batch = self._pending_batches.get(batch_key, [])
        self._pending_batches[batch_key] = []
        return batch
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        by_priority = defaultdict(int)
        by_type = defaultdict(int)
        
        for req in self._queue:
            by_priority[req.priority.name] += 1
            by_type[req.decision_type.value] += 1
        
        # Calculate SLAs
        sla_violations = 0
        now = datetime.now(UTC)
        for req in self._queue:
            if req.deadline and now > req.deadline:
                sla_violations += 1
        
        return {
            "queue_depth": len(self._queue),
            "by_priority": dict(by_priority),
            "by_type": dict(by_type),
            "batched_pending": sum(len(b) for b in self._pending_batches.values()),
            "auto_approval_rate": (
                self._stats["auto_approved"] / max(1, self._stats["submitted"])
            ),
            "avg_decision_time_ms": self._stats["avg_decision_time_ms"],
            "sla_violations": sla_violations,
            **self._stats
        }
    
    def on_auto_approve(self, callback: Callable[[HITLRequest], None]):
        """Register callback for auto-approval events."""
        self._on_auto_approve.append(callback)
    
    def on_human_required(self, callback: Callable[[HITLRequest], None]):
        """Register callback for human review requests."""
        self._on_human_required.append(callback)
    
    def on_batch_ready(self, callback: Callable[[str, List[HITLRequest]], None]):
        """Register callback for batch ready events."""
        self._on_batch_ready.append(callback)
    
    def add_auto_approval_rule(self, rule: AutoApprovalRule):
        """Add a custom auto-approval rule."""
        self._auto_approval_rules.append(rule)
    
    def enable_auto_approval(self, enabled: bool = True):
        """Enable or disable auto-approval."""
        self.auto_approval_enabled = enabled
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific request."""
        if request_id in self._decisions:
            decision = self._decisions[request_id]
            return {
                "status": "completed",
                "decision": decision.decision,
                "approved": decision.approved,
                "reviewer": decision.reviewer_id,
                "decided_at": decision.decided_at.isoformat()
            }
        
        if request_id in self._requests:
            request = self._requests[request_id]
            position = self._get_queue_position(request_id)
            return {
                "status": "pending" if position >= 0 else "queued",
                "position": position if position >= 0 else None,
                "priority": request.priority.name,
                "wait_time_seconds": self._estimate_wait_time(request)
            }
        
        return None
