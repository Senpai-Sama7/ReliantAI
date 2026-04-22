# Metacognitive Autonomy Layer (MAL) — Usage Guide

Make ReliantAI **intuitive, self-improving, self-healing, and autonomously learning**.

---

## Quick Start

### 1. Start the Autonomy System

```bash
cd integration/metacognitive_layer
python main.py
```

This starts all four components:
- 🧠 **Metacognitive Engine** — Observes and learns patterns
- 🔧 **Self-Healing Orchestrator** — Monitors and auto-remediates
- 📊 **Feedback Collector** — Extracts insights from every interaction
- 🔮 **Intent Predictor** — Anticipates needs before articulated

### 2. Instrument Your Services

Add these calls to your services to enable autonomy:

```python
from integration.metacognitive_layer.main import (
    observe_event,
    record_activity,
    collect_feedback,
    get_jit_recommendations
)

# In your API endpoints:
async def your_endpoint(request):
    start_time = time.time()
    
    try:
        result = await process_request(request)
        
        # Observe success
        await observe_event(
            service='your-service',
            operation='your_operation',
            status='success',
            duration_ms=(time.time() - start_time) * 1000
        )
        
        # Record for intent prediction
        await record_activity(
            service='your-service',
            operation='your_operation',
            user_id=request.user_id
        )
        
        return result
        
    except Exception as e:
        # Collect failure feedback
        await collect_feedback(
            source_service='your-service',
            source_operation='your_operation',
            feedback_type='failure',
            error=str(e),
            input_context=request.dict()
        )
        raise
```

### 3. Access Autonomous Insights

```python
from integration.metacognitive_layer.main import (
    get_applicable_insights,
    get_jit_recommendations,
    get_mal_system
)

# Get insights for current context
insights = await get_applicable_insights({
    'service': 'your-service',
    'operation': 'current_operation',
    'user_id': 'user-123'
})

# Get JIT recommendations
recommendations = await get_jit_recommendations()

# Get full system status
mal = await get_mal_system()
status = mal.get_status()
```

---

## Core Concepts

### The Metacognition Loop (Every 30 seconds)

```
OBSERVE → ANALYZE → LEARN → ADAPT → PREDICT → PREPARE → EXECUTE
   ↑                                               ↓
   └──────────── FEEDBACK ← OUTCOMES ← ACTIONS ────┘
```

### Cognitive Budget

The system has limited "attention" — it prioritizes:
1. **Error events** (highest priority)
2. **Slow operations** (> 1 second)
3. **Unusual patterns** (off-hours activity)
4. **Common operations** (batch learning)

### Confidence Levels

| Confidence | Action |
|------------|--------|
| **≥ 95%** | Execute automatically |
| **85-95%** | Execute with notification |
| **70-85%** | Prepare resources, ask confirmation |
| **50-70%** | Log prediction, observe only |
| **< 50%** | Need more training data |

---

## Component Details

### 1. Metacognitive Engine

**Purpose:** Pattern recognition and prediction

**What It Does:**
- Observes all system events via Event Bus
- Recognizes recurring patterns
- Updates confidence scores (Bayesian learning)
- Generates predictions about system behavior

**Key Methods:**
```python
# Observe any event
await observe_event(
    service='money',
    operation='dispatch_created',
    status='success',
    duration_ms=150
)

# Subscribe to autonomy decisions
engine.subscribe(lambda event: print(event))

# Get insights
insights = engine.get_insights()
```

**Database Tables:**
- `telemetry_events` — Raw observations
- `learned_patterns` — Extracted patterns
- `predictions` — Generated predictions with outcomes

### 2. Self-Healing Orchestrator

**Purpose:** Detect and auto-remediate failures

**Healing Response Times:**

| Severity | Response | Actions |
|----------|----------|---------|
| **CRITICAL** | < 5 seconds | Auto-restart, escalate |
| **WARNING** | < 60 seconds | Adjust resources, notify |
| **DEGRADED** | < 5 minutes | Route around, schedule maintenance |
| **ANOMALY** | Next cycle | Log pattern, watch for recurrence |

**Key Methods:**
```python
# Report critical failure
await report_critical_failure(
    service='apex-mcp',
    error='Connection pool exhausted',
    context={'current_connections': 100}
)

# Get healing stats
stats = orchestrator.get_healing_stats()
```

**Monitored Services:**
- auth (port 8080)
- event-bus (port 8081)
- apex-mcp (port 4000)
- money (port 8000)
- b-a-p (port 8000)

**Healing Actions:**
- `RESTART_SERVICE` — Graceful restart
- `CIRCUIT_BREAKER` — Activate circuit breaker
- `POOL_RESET` — Reset DB connection pools
- `CACHE_INVALIDATE` — Clear and warm cache
- `ESCALATE_HUMAN` — Alert operators

### 3. Feedback Collector

**Purpose:** Extract reusable knowledge from every interaction

**Feedback Types:**
```python
SUCCESS              # Task completed as expected
PARTIAL             # Task completed with workarounds
FAILURE             # Task failed, manual intervention
TIMEOUT             # Task exceeded time budget
EXCEPTION           # Unexpected error
USER_CORRECTION     # User had to fix output
OPTIMIZATION        # Task ran slower than baseline
POSITIVE_REINFORCEMENT  # Explicit praise
NEGATIVE_REINFORCEMENT  # Explicit complaint
```

**Key Methods:**
```python
# Report success
signal_id = await collect_feedback(
    source_service='cleardesk',
    source_operation='document_process',
    feedback_type='success',
    duration_ms=2500,
    user_id='user-123'
)

# Report user correction (very valuable for learning!)
await collect_feedback(
    source_service='money',
    source_operation='technician_suggestion',
    feedback_type='user_correction',
    original={'technician_id': 'tech-1'},
    corrected={'technician_id': 'tech-3'},
    expectation_gap='User manually reassigned to tech-3'
)

# Get applicable insights
insights = await get_applicable_insights({
    'service': 'money',
    'operation': 'dispatch'
})
```

**Insight Types:**
- **failure_pattern** — Common failure modes
- **successful_path** — Decision sequences that succeed
- **optimization_opportunity** — Slow operations to optimize

### 4. Intent Predictor

**Purpose:** Anticipate needs before articulated

**Prediction Types:**
- `USER_INTENT` — What user will likely do next
- `LOAD_SPIKE` — Incoming traffic surge
- `RESOURCE_NEED` — Capacity requirements
- `OPTIMAL_ROUTE` — Best system for request
- `CACHE_OPPORTUNITY` — Data likely to be needed
- `FAILURE_RISK` — Service likely to fail

**Key Methods:**
```python
# Record activity for pattern learning
await record_activity(
    service='cleardesk',
    operation='login',
    user_id='user-123'
)

# Get JIT recommendations
recommendations = await get_jit_recommendations()
# Returns: [{'action': 'pre_fetch_data', 'confidence': 0.85, ...}]

# Check prediction accuracy
accuracy = predictor.get_prediction_accuracy()
# Returns: {'accuracy': 0.82, 'total_validated': 150, ...}
```

**Common Predictions:**
- User logs in → Will check recent documents (85% confidence)
- Dispatch created → Will need technician matching (90% confidence)
- Upload document → Will review within 2 minutes (80% confidence)
- 9 AM Monday → Money dispatch surge incoming (75% confidence)

---

## Integration Examples

### Example 1: ClearDesk Document Processing

```python
from integration.metacognitive_layer.main import (
    observe_event, record_activity, collect_feedback
)

async def process_document(doc_id: str, user_id: str):
    start = time.time()
    
    try:
        # Pre-warm based on prediction
        recommendations = await get_jit_recommendations()
        for rec in recommendations:
            if rec['action'] == 'pre_fetch_data':
                await warm_cache(rec['params'])
        
        # Process
        result = await ai_extract_data(doc_id)
        
        # Observe success
        duration = (time.time() - start) * 1000
        await observe_event(
            service='cleardesk',
            operation='document_process',
            status='success',
            duration_ms=duration
        )
        
        # Record activity for next prediction
        await record_activity(
            service='cleardesk',
            operation='document_process',
            user_id=user_id
        )
        
        return result
        
    except Exception as e:
        await collect_feedback(
            source_service='cleardesk',
            source_operation='document_process',
            feedback_type='failure',
            error=str(e),
            input_context={'doc_id': doc_id}
        )
        raise
```

### Example 2: Money Dispatch with Self-Healing

```python
async def create_dispatch(dispatch_request):
    start = time.time()
    
    try:
        dispatch = await dispatch_crew.process(dispatch_request)
        
        await observe_event(
            service='money',
            operation='dispatch_create',
            status='success',
            duration_ms=(time.time() - start) * 1000
        )
        
        # Record for intent prediction
        await record_activity(
            service='money',
            operation='dispatch_create',
            context={'urgency': dispatch_request.urgency}
        )
        
        return dispatch
        
    except Exception as e:
        # This triggers both healing and learning
        await report_critical_failure(
            service='money',
            error=str(e),
            context={'operation': 'dispatch_create'}
        )
        raise
```

### Example 3: B-A-P Analytics with User Feedback

```python
async def generate_report(user_id: str, query: str):
    start = time.time()
    
    report = await analytics_engine.generate(query)
    duration = (time.time() - start) * 1000
    
    # Observe
    await observe_event(
        service='b-a-p',
        operation='report_generate',
        status='success',
        duration_ms=duration
    )
    
    # User feedback endpoint
    @app.post("/feedback/report/{report_id}")
    async def report_feedback(report_id: str, rating: int, correction: Optional[dict] = None):
        if correction:
            await collect_feedback(
                source_service='b-a-p',
                source_operation='report_generate',
                feedback_type='user_correction',
                original=report.to_dict(),
                corrected=correction,
                satisfaction_score=rating
            )
        else:
            await collect_feedback(
                source_service='b-a-p',
                source_operation='report_generate',
                feedback_type='positive_reinforcement' if rating > 7 else 'partial',
                satisfaction_score=rating
            )
```

---

## Monitoring & Debugging

### Get System Status

```python
mal = await get_mal_system()
status = mal.get_status()

print(f"Patterns learned: {status['engine']['patterns_learned']}")
print(f"Healing events (24h): {status['healing']['healing_events_24h']}")
print(f"Active insights: {status['feedback']['active_insights']}")
print(f"Prediction accuracy: {status['predictor']['accuracy']:.1%}")
print(f"JIT recommendations: {len(status['jit_recommendations'])}")
```

### Query Database Directly

```bash
# Check recent telemetry
psql -d metacognitive -c "SELECT service, operation, status, COUNT(*) FROM telemetry_events WHERE timestamp > NOW() - INTERVAL '1 hour' GROUP BY 1,2,3;"

# Check learned patterns
psql -d metacognitive -c "SELECT pattern_type, success_rate, confidence_score, occurrence_count FROM learned_patterns WHERE confidence_score > 0.7 ORDER BY confidence_score DESC;"

# Check healing actions
psql -d metacognitive -c "SELECT service, action_taken, outcome, time_to_recovery_ms FROM healing_actions WHERE triggered_at > NOW() - INTERVAL '24 hours';"

# Check prediction accuracy
psql -d metacognitive -c "SELECT prediction_type, AVG(CASE WHEN was_correct THEN 1 ELSE 0 END) as accuracy, COUNT(*) FROM predictions WHERE was_correct IS NOT NULL GROUP BY 1;"
```

### View Logs

```bash
# MAL system logs
tail -f /var/log/reliantai/mal.log

# Or with systemd
journalctl -u reliantai-mal -f
```

---

## Configuration

### Environment Variables

```bash
# Database
METACOGNITIVE_DB_URL=postgresql://localhost:5435/metacognitive

# Processing intervals (seconds)
MAL_OBSERVATION_INTERVAL=30
MAL_PREDICTION_INTERVAL=60
MAL_FEEDBACK_INTERVAL=60
MAL_HEALING_INTERVAL=10

# Confidence thresholds
MAL_CRITICAL_CONFIDENCE=0.95
MAL_HIGH_CONFIDENCE=0.85
MAL_MEDIUM_CONFIDENCE=0.70

# Healing
MAL_AUTO_HEAL_CRITICAL=true
MAL_NOTIFY_ON_WARNING=true
MAL_ESCALATION_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Database Setup

```bash
# Create database
psql -c "CREATE DATABASE metacognitive;"

# Tables auto-created on first run, or:
cd integration/metacognitive_layer
python -c "from main import get_mal_system; import asyncio; asyncio.run(get_mal_system().initialize())"
```

---

## Best Practices

### 1. Instrument Everything

Add `observe_event()` calls to:
- Every API endpoint
- Every background job
- Every external API call
- Every cache operation

### 2. Capture User Feedback

Most valuable feedback types:
1. **USER_CORRECTION** — User fixed something the system did
2. **NEGATIVE_REINFORCEMENT** — User complained
3. **POSITIVE_REINFORCEMENT** — User praised

### 3. Handle Failures Explicitly

Always use `report_critical_failure()` for:
- Exceptions that bubble up to API layer
- Service unavailability
- Timeout errors
- Resource exhaustion

### 4. Review Weekly

```bash
# Weekly autonomy report
python -c "
from integration.metacognitive_layer.main import get_mal_system
import asyncio

async def report():
    mal = await get_mal_system()
    status = mal.get_status()
    print('=== Weekly MAL Report ===')
    print(f\"Patterns: {status['engine']['patterns_learned']}\")
    print(f\"Insights: {status['feedback']['active_insights']}\")
    print(f\"Accuracy: {status['predictor']['accuracy']:.1%}\")
    print(f\"Healed: {status['healing']['healing_events_24h']} in last 24h\")

asyncio.run(report())
"
```

---

## Troubleshooting

### Issue: No Patterns Being Learned

**Check:** Are you calling `observe_event()`?
```bash
# Check if telemetry is flowing
psql -c "SELECT COUNT(*) FROM telemetry_events WHERE timestamp > NOW() - INTERVAL '1 hour';"
# Should be > 0
```

### Issue: Predictions Always Wrong

**Check:** Is validation running?
```bash
psql -c "SELECT COUNT(*), SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) FROM predictions WHERE was_correct IS NOT NULL;"
# Should have validated predictions
```

### Issue: Healing Not Triggering

**Check:** Are services registered?
```python
orchestrator = await get_orchestrator()
print(orchestrator.health_monitor._health_checks.keys())
# Should list your services
```

---

## Future Enhancements

### Phase 2: Deep Learning
- Neural nets for pattern recognition
- Embedding-based similarity matching
- Multi-modal learning (telemetry + feedback + predictions)

### Phase 3: Collective Intelligence
- Cross-tenant pattern sharing (privacy preserving)
- Industry-wide optimization suggestions
- Pre-trained models for common scenarios

### Phase 4: Natural Language
- "Why did you do that?" explanations
- "What will happen if...?" simulation
- "Teach me to..." guided improvement

---

**Version:** 1.0  
**Created:** 2026-04-18  
**Status:** Production Ready
