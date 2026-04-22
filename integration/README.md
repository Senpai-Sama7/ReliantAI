# ReliantAI Integration Layer

This directory contains the integration infrastructure for the ReliantAI platform.

## Structure

- `auth/` - OAuth2/JWT authentication service
- `gateway/` - API gateway and routing
- `events/` - Event bus and message broker
- `observability/` - Monitoring, logging, and tracing
- `tests/` - Integration tests

## Getting Started

See `/home/donovan/Projects/ReliantAI/PROGRESS_TRACKER.md` for detailed implementation steps.

## Quick Start

### 1. Auth Service
```bash
cd auth
pip install -r requirements.txt
python auth_server.py
```

### 2. Event Bus
```bash
cd events
redis-server  # In separate terminal
pip install redis pydantic
python -c "from event_bus import EventBus; print('Event bus ready')"
```

## Documentation

- **Progress Tracker:** `/home/donovan/Projects/ReliantAI/PROGRESS_TRACKER.md`
- **Build Rules:** `/home/donovan/Projects/ReliantAI/AGENTS.md`
- **Integration Plan:** `/home/donovan/Projects/ReliantAI/integration_plan/V.md`
