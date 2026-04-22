# Event Bus

Redis-based event bus for inter-service communication.

## Features

- Pub/sub messaging pattern
- Event persistence (24-hour TTL)
- Schema validation with Pydantic
- Dead letter queue for failed events

## Setup

```bash
# Start Redis
redis-server

# Install dependencies
pip install redis pydantic

# Use event bus
python -c "from event_bus import EventBus; bus = EventBus(); print('Ready')"
```

## Testing

```bash
pytest test_event_bus.py -v
```

See PROGRESS_TRACKER.md Task 0.2.2 for complete implementation.
