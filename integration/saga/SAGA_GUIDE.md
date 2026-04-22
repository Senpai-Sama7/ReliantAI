# Saga Pattern Guide - Distributed Transaction Coordination

## Overview

The Saga Orchestrator provides distributed transaction support for the ReliantAI platform. A saga is a sequence of local transactions where each transaction updates data within a single service, and the saga coordinates these transactions across multiple services.

## Key Concepts

### Saga Pattern
```
Saga = Sequence of Steps + Compensation Logic

If any step fails:
    - Compensate completed steps (undo)
    - Mark saga as failed

If all steps succeed:
    - Mark saga as completed
```

### Components

| Component | Purpose |
|-----------|---------|
| `Saga` | Container for workflow steps |
| `SagaStep` | Individual operation with compensation |
| `SagaOrchestrator` | Execution engine |
| `Redis` | State persistence + idempotency |
| `Kafka` | Event publishing |

## Usage Example

```python
from integration.saga.saga_orchestrator import (
    SagaOrchestrator, SagaStep, SagaStatus
)

# Define saga steps
steps = [
    SagaStep(
        step_id="1",
        name="Reserve Payment",
        service="money",
        action="reserve_payment",
        compensation_action="release_payment",
        payload={"amount": 100, "customer_id": "123"}
    ),
    SagaStep(
        step_id="2",
        name="Dispatch Technician",
        service="money",
        action="dispatch_hvac",
        compensation_action="cancel_dispatch",
        payload={"location": "Houston", "urgency": "high"}
    ),
    SagaStep(
        step_id="3",
        name="Notify Customer",
        service="apex",
        action="send_notification",
        compensation_action=None,  # No compensation needed
        payload={"channel": "sms", "message": "Technician dispatched"}
    )
]

# Execute saga
saga_id = await orchestrator.execute_saga(
    saga_type="hvac_booking",
    steps=steps,
    correlation_id="booking-123",
    tenant_id="tenant-abc"
)

# Check status
status = await orchestrator.get_saga_status(saga_id)
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/saga` | POST | Create new saga |
| `/saga/{id}` | GET | Get saga status |
| `/saga/{id}/compensate` | POST | Manual compensation |
| `/metrics` | GET | Prometheus metrics |

## State Machine

```
PENDING → RUNNING → COMPLETED
            ↓
         FAILED
            ↓
      COMPENSATING
            ↓
       COMPENSATED
```

## Compensation Rules

1. **Compensation is required** for any step that modifies state
2. **Idempotency keys** prevent double-execution
3. **Compensation order** is reverse of execution order
4. **Partial compensation** is possible (some steps may fail to compensate)

## Resilience Features

| Feature | Implementation |
|---------|---------------|
| Idempotency | Redis key: `saga:{saga_id}:step:{step_id}` |
| Retries | Max 3 retries per step |
| Timeout | 300s default, configurable |
| Dead Letter | Failed sagas logged to Kafka |
| Metrics | Prometheus counters + histograms |

## Monitoring

### Key Metrics

```prometheus
# Saga counts
saga_started_total{saga_type="hvac_booking"}
saga_completed_total{saga_type="hvac_booking"}
saga_failed_total{saga_type="hvac_booking",reason="step_failure"}
saga_compensated_total{saga_type="hvac_booking"}

# Duration
saga_duration_seconds{saga_type="hvac_booking"}

# Active
active_sagas
```

### Health Check

```bash
curl http://saga-orchestrator:8080/health
```

## Common Patterns

### HVAC Booking Saga
```
1. Reserve Payment (Money)
2. Check Tech Availability (Money)
3. Dispatch Technician (Money)
4. Send Confirmation (APEX)
5. Schedule Follow-up (APEX)
```

### Lead Handoff Saga
```
1. Score Lead (Ops Intelligence)
2. Create Dispatch (Money)
3. Notify Sales (APEX)
4. Update CRM (APEX/Citadel)
```

## Testing

```bash
# Run saga tests
cd integration/tests
pytest saga_tests.py -v

# Load test
locust -f saga_load_test.py
```

## Troubleshooting

### Issue: Saga stuck in RUNNING
- Check: `active_sagas` metric
- Action: Check service health, may need manual intervention

### Issue: Compensation fails
- Check: `saga_compensated_total` counter
- Action: Review compensation logic, may need manual cleanup

### Issue: Duplicate execution
- Check: Idempotency keys in Redis
- Action: Verify idempotency key generation

## Best Practices

1. **Keep steps small** - Easier to compensate
2. **Design compensations first** - Before writing action logic
3. **Use idempotency keys** - Always
4. **Monitor compensation rates** - High rate indicates design issues
5. **Test failure scenarios** - Not just happy path

## Integration with Other Systems

| System | Integration Point |
|--------|-------------------|
| Money | `/dispatch`, `/payment` |
| APEX | `/agents/layer3/dispatch` |
| Citadel | `/chat`, `/tools` |
| Event Bus | Kafka topic: `saga.events` |

## Future Enhancements

- [ ] Parallel step execution
- [ ] Saga composition (sagas calling sagas)
- [ ] Timeout compensation strategies
- [ ] Visual saga designer
- [ ] Automatic compensation testing
