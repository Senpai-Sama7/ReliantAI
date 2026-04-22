# Metacognitive Autonomy Layer - Integration Tests

Comprehensive test suite for the self-improving, self-healing autonomous system.

## Test Structure

```
tests/
├── __init__.py              # Test package
├── conftest.py            # Shared fixtures
├── test_engine.py         # Pattern recognition tests
├── test_healing.py        # Self-healing tests
├── test_optimizer.py      # Autonomous optimization tests
├── test_consolidator.py   # Knowledge consolidation tests
└── test_integration.py    # End-to-end integration tests
```

## Running Tests

```bash
# All tests
cd /home/donovan/Projects/platforms/ReliantAI/integration
pytest metacognitive_layer/tests/ -v

# Specific component
pytest metacognitive_layer/tests/test_engine.py -v
pytest metacognitive_layer/tests/test_healing.py -v

# With coverage
pytest metacognitive_layer/tests/ --cov=metacognitive_layer --cov-report=html
```

## Test Coverage

### Engine Tests (`test_engine.py`)
- Pattern confidence updates (Bayesian)
- Cognitive budget allocation
- Observation buffering
- Prediction actionability
- Pattern type inference

### Healing Tests (`test_healing.py`)
- Symptom detection
- Diagnosis rules
- Health threshold monitoring
- Service restart commands
- Healing statistics

### Optimizer Tests (`test_optimizer.py`)
- Cache optimization strategies
- Performance baseline comparison
- Safety threshold enforcement
- Status transitions
- Metrics history limits

### Consolidator Tests (`test_consolidator.py`)
- Pattern materialization criteria
- API sequence detection
- Tool combination extraction
- Query normalization
- Knowledge confidence scoring

### Integration Tests (`test_integration.py`)
- Full MAL system initialization
- End-to-end observation flow
- Feedback to consolidation pipeline
- Cross-component metrics flow
- Concurrent operations
- Error handling

## Fixtures

The `conftest.py` provides mocked database pools and component instances for isolated testing.

## Requirements

```
pytest
pytest-asyncio
pytest-cov
asyncpg
```

## CI Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Run MAL Tests
  run: |
    cd integration
    pytest metacognitive_layer/tests/ -v --cov=metacognitive_layer
```
