# Metacognitive Autonomy Layer (MAL) — Architecture

**Vision:** Transform ReliantAI from reactive to proactive — a system that learns from every interaction, heals itself before failures cascade, and anticipates needs before they're articulated.

---

## Core Philosophy

### From Reactive → Proactive → Predictive

```
Reactive:    User reports issue → System investigates → Fix deployed
Proactive:   System detects anomaly → Auto-remediates → Notifies user
Predictive:  System predicts need → Pre-deploys resources → User confirms
```

### The Metacognition Loop

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      METACOGNITIVE LOOP (Every 30s)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   OBSERVE → ANALYZE → LEARN → ADAPT → PREDICT → PREPARE → EXECUTE       │
│      ↑                                                            ↓       │
│      └──────────────── FEEDBACK ← RESULTS ← ACTIONS ──────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## System Components

### 1. Metacognitive Engine (Layer 5 of APEX)

**Location:** `integration/metacognitive_layer/engine.py`

**Purpose:** The "brain" that observes all system operations and makes autonomy decisions.

**Functions:**
- Pattern recognition across Event Bus telemetry
- Performance trend analysis
- Anomaly detection with statistical models
- Decision confidence scoring
- Action prioritization

**Key Concept:** **Cognitive Budget**
- System has limited "attention" (compute/time budget)
- MAL prioritizes which observations deserve deep analysis
- Low-confidence predictions get more resources
- High-confidence patterns run autonomously

### 2. Self-Healing Orchestrator

**Location:** `integration/metacognitive_layer/healing_orchestrator.py`

**Purpose:** Detect failures before they cascade and auto-remediate.

**Healing Strategies:**

| Severity | Response Time | Action |
|----------|--------------|--------|
| **Critical** | < 5s | Auto-restart service, escalate to human |
| **Warning** | < 60s | Adjust resources, notify ops |
| **Degraded** | < 5min | Route around, schedule maintenance |
| **Anomaly** | Next cycle | Log pattern, watch for recurrence |

**Recovery Actions:**
- Service restart with exponential backoff
- Circuit breaker pattern activation
- Failover to backup instances
- Configuration rollback
- Database connection pool reset
- Cache invalidation and warmup

### 3. Feedback Loop System

**Location:** `integration/metacognitive_layer/feedback_collector.py`

**Purpose:** Capture success/failure signals from every system interaction.

**Feedback Types:**

```python
class FeedbackSignal:
    SIGNAL_TYPES = {
        "SUCCESS": "Task completed as expected",
        "PARTIAL": "Task completed with workarounds",
        "FAILURE": "Task failed, manual intervention required",
        "TIMEOUT": "Task exceeded time budget",
        "EXCEPTION": "Unexpected error occurred",
        "USER_CORRECTION": "User had to manually fix output",
        "OPTIMIZATION": "Task ran slower than baseline",
    }
```

**Learning Pipeline:**
1. **Collect:** Every API call, tool execution, agent decision
2. **Correlate:** Link cause → effect → outcome
3. **Extract:** Identify what led to success vs failure
4. **Update:** Adjust decision weights, cache strategies, routing logic
5. **Validate:** A/B test new behavior against baseline

### 4. JIT Intent Prediction Engine

**Location:** `integration/metacognitive_layer/intent_predictor.py`

**Purpose:** Anticipate user needs before they articulate them.

**Prediction Models:**

| Context Signal | Likely Intent | Pre-Action |
|---------------|---------------|------------|
| User opens ClearDesk 3x at 9am | Morning document review | Pre-load yesterday's invoices |
| Money dispatch queue > 10 | Dispatch surge incoming | Pre-scale technician matching |
| B-A-P query: "revenue last month" | Trend analysis incoming | Pre-compute month comparisons |
| High error rate on specific API | Service degradation | Pre-route to backup instance |

**Prediction Confidence Thresholds:**
- **> 90%:** Execute automatically, notify user
- **70-90%:** Prepare resources, ask user to confirm
- **50-70%:** Log prediction, observe if user confirms
- **< 50%:** Don't act, collect more training data

### 5. Autonomous Optimization Scheduler

**Location:** `integration/metacognitive_layer/optimizer.py`

**Purpose:** Continuously optimize system performance without human intervention.

**Optimization Domains:**

```
Performance:
- Cache TTL tuning based on hit rates
- Database query plan caching
- Connection pool sizing
- Batch processing window optimization

Resources:
- Memory allocation per service
- CPU prioritization
- Disk cleanup scheduling
- Network timeout tuning

Costs:
- API call batching
- Result caching strategies
- Lazy loading thresholds
- Compression algorithm selection
```

**Safety Constraints:**
- Never optimize during peak hours without rollback plan
- Always A/B test with 10% traffic first
- Rollback if error rate increases > 0.1%
- Human approval for infrastructure changes

### 6. Knowledge Consolidation Service

**Location:** `integration/metacognitive_layer/knowledge_consolidator.py`

**Purpose:** Extract reusable patterns from successful operations.

**What It Does:**
- Identifies common query patterns → Creates materialized views
- Detects frequent API sequences → Creates composite endpoints
- Finds successful agent tool combinations → Creates skill shortcuts
- Learns optimal parameter values → Creates tuned defaults

---

## Data Architecture

### Metacognitive Database Schema

```sql
-- Telemetry Store (Time-series, 30-day retention)
CREATE TABLE telemetry_events (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    service VARCHAR(64),
    operation VARCHAR(128),
    duration_ms INTEGER,
    status VARCHAR(32),
    metadata JSONB,
    context_hash VARCHAR(64)
);

-- Pattern Store (Long-term learning)
CREATE TABLE learned_patterns (
    id UUID PRIMARY KEY,
    pattern_type VARCHAR(64),
    pattern_signature VARCHAR(256),
    success_rate FLOAT,
    avg_duration_ms INTEGER,
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    occurrence_count INTEGER,
    confidence_score FLOAT
);

-- Prediction Log (For validation)
CREATE TABLE predictions (
    id UUID PRIMARY KEY,
    predicted_at TIMESTAMPTZ,
    prediction_type VARCHAR(64),
    confidence FLOAT,
    predicted_action JSONB,
    actual_outcome JSONB,
    was_correct BOOLEAN,
    user_confirmed BOOLEAN
);

-- Healing Actions Log
CREATE TABLE healing_actions (
    id UUID PRIMARY KEY,
    triggered_at TIMESTAMPTZ,
    service VARCHAR(64),
    symptom VARCHAR(256),
    diagnosis VARCHAR(256),
    action_taken JSONB,
    outcome VARCHAR(32),
    time_to_recovery_ms INTEGER
);
```

---

## Integration Points

### Event Bus Integration

```python
# MAL subscribes to all events
MAL_SUBSCRIPTIONS = [
    "dispatch.completed",      # → Learn dispatch patterns
    "document.processed",      # → Learn processing times
    "analytics.recorded",      # → Learn query patterns
    "agent.task.completed",    # → Learn agent performance
    "system.error",           # → Trigger healing
    "api.request",            # → Collect telemetry
    "cache.hit",              # → Optimize caching
    "cache.miss",             # → Pre-warm cache
]
```

### APEX Integration

```python
# Layer 5: Metacognitive Layer
class Layer5MetacognitiveAgent:
    """
    Fifth layer of APEX that monitors all lower layers
    and makes autonomy decisions.
    """
    
    async def on_every_decision(self, layer1_4_context):
        # Observe the decision being made
        # Predict if it will succeed
        # Suggest optimizations
        # Learn from the outcome
        pass
```

### Cross-System Orchestrator Integration

```python
# MAL provides intelligence to orchestrator
class IntelligentOrchestrator(CrossSystemOrchestrator):
    async def route_task(self, task):
        # Get MAL's prediction of best target system
        prediction = await mal.predict_optimal_route(task)
        
        # If confidence high, auto-route
        # If confidence medium, suggest to user
        # If confidence low, use traditional routing
```

---

## Safety & Ethics

### Autonomy Guardrails

1. **Human-in-the-Loop for:**
   - Infrastructure changes (restart, scale, migrate)
   - Security policy modifications
   - Data retention/deletion
   - Budget-impacting decisions

2. **Automatic Rollback Triggers:**
   - Error rate increases > threshold
   - User complaints within 1 hour of change
   - Performance degradation > 20%
   - Unexplained resource spikes

3. **Transparency Requirements:**
   - All autonomous actions logged with rationale
   - Dashboard showing "Why system did X"
   - Weekly summary of autonomy decisions
   - Opt-out capability for any automated feature

### Bias Detection

- Monitor for patterns that disadvantage certain user types
- A/B test autonomy decisions for fairness
- Regular audits of learned patterns
- Diverse training data requirements

---

## Success Metrics

### Self-Improvement KPIs

| Metric | Baseline | Target |
|--------|----------|--------|
| Prediction accuracy | 0% | > 85% |
| Learning cycle time | N/A | < 1 hour |
| Pattern extraction | Manual | Automatic |

### Self-Healing KPIs

| Metric | Baseline | Target |
|--------|----------|--------|
| Mean time to detection | 5 min | < 30s |
| Mean time to recovery | 30 min | < 5 min |
| False positive rate | N/A | < 5% |
| Uptime improvement | 99.9% | 99.99% |

### JIT Effectiveness KPIs

| Metric | Baseline | Target |
|--------|----------|--------|
| Pre-warm hit rate | 0% | > 70% |
| User confirmation rate | N/A | > 80% |
| Perceived latency | 500ms | < 200ms |

---

## Implementation Phases

### Phase 1: Observation (Week 1)
- Deploy telemetry collector
- Build pattern recognition baseline
- Create prediction models (simple heuristics)

### Phase 2: Learning (Week 2-3)
- Feedback loop integration
- Pattern consolidation service
- A/B testing framework

### Phase 3: Healing (Week 3-4)
- Health monitoring with thresholds
- Automated remediation playbooks
- Circuit breaker auto-tuning

### Phase 4: Prediction (Week 4-5)
- Intent prediction models
- Pre-warming strategies
- JIT resource allocation

### Phase 5: Full Autonomy (Week 5-6)
- Metacognitive engine deployment
- Autonomous optimization
- Human-in-the-loop refinement

---

**Document:** MAL Architecture v1.0  
**Created:** 2026-04-18  
**Status:** Design Complete → Ready for Implementation
