#!/bin/bash
# ReliantAI Integration - Quick Start Script
# This script executes Task 0.1.1: Create Integration Infrastructure Directory

set -e  # Exit on error

echo "=================================================="
echo "ReliantAI Integration - Phase 0 Setup"
echo "Task 0.1.1: Create Integration Infrastructure"
echo "=================================================="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INTEGRATION_DIR="$SCRIPT_DIR/integration"

echo "Creating integration directory structure..."
mkdir -p "$INTEGRATION_DIR"/{auth,gateway,events,observability,tests}

echo "Initializing git repository..."
cd "$INTEGRATION_DIR"
if [ ! -d ".git" ]; then
    git init
    echo "Git repository initialized"
else
    echo "Git repository already exists"
fi

echo "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
*.pyc
__pycache__/
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/

# Virtual environments
venv/
.venv/
env/
ENV/

# Environment variables
.env
.env.local
*.env

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Redis
dump.rdb

# Temporary files
*.tmp
*.temp
EOF

echo "Creating README.md..."
cat > README.md << 'EOF'
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
EOF

echo "Creating directory READMEs..."

# Auth directory README
cat > auth/README.md << 'EOF'
# Authentication Service

OAuth2/JWT authentication service for ReliantAI platform.

## Features

- OAuth2 authorization code and client credentials flows
- JWT access and refresh tokens
- Role-Based Access Control (RBAC)
- User and service account management

## Setup

```bash
pip install -r requirements.txt
python auth_server.py
```

## Testing

```bash
pytest test_auth.py -v
```

## API Endpoints

- `POST /register` - Register new user
- `POST /token` - Login and get tokens
- `POST /refresh` - Refresh access token
- `GET /verify` - Verify token validity

See PROGRESS_TRACKER.md Task 0.2.1 for complete implementation.
EOF

# Events directory README
cat > events/README.md << 'EOF'
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
EOF

# Gateway directory README
cat > gateway/README.md << 'EOF'
# API Gateway

Central API gateway for routing requests to ReliantAI services.

## Status

🔴 NOT IMPLEMENTED - See PROGRESS_TRACKER.md Phase 1
EOF

# Observability directory README
cat > observability/README.md << 'EOF'
# Observability Stack

Monitoring, logging, and tracing infrastructure.

## Planned Components

- Grafana dashboards
- Prometheus metrics
- Loki log aggregation
- Jaeger distributed tracing

## Status

🔴 NOT IMPLEMENTED - See PROGRESS_TRACKER.md Phase 4
EOF

# Tests directory README
cat > tests/README.md << 'EOF'
# Integration Tests

End-to-end integration tests for the ReliantAI platform.

## Test Categories

- Authentication flow tests
- Event bus integration tests
- Cross-service workflow tests
- Performance and load tests

## Running Tests

```bash
pytest -v
```

## Status

🟡 IN PROGRESS - Tests added as components are implemented
EOF

echo ""
echo "✅ Integration infrastructure created successfully!"
echo ""
echo "Directory structure:"
tree -L 2 "$INTEGRATION_DIR" 2>/dev/null || find "$INTEGRATION_DIR" -maxdepth 2 -type d

echo ""
echo "=================================================="
echo "Next Steps:"
echo "=================================================="
echo ""
echo "1. Review the structure:"
echo "   cd $INTEGRATION_DIR"
echo "   ls -la"
echo ""
echo "2. Implement Auth Service (Task 0.2.1):"
echo "   cd auth"
echo "   # Copy code from PROGRESS_TRACKER.md"
echo ""
echo "3. Implement Event Bus (Task 0.2.2):"
echo "   cd events"
echo "   # Copy code from PROGRESS_TRACKER.md"
echo ""
echo "4. Update PROGRESS_TRACKER.md:"
echo "   # Mark Task 0.1.1 as complete"
echo "   # Add timestamp and proof"
echo ""
echo "=================================================="
echo "Documentation:"
echo "=================================================="
echo "- Progress Tracker: $SCRIPT_DIR/PROGRESS_TRACKER.md"
echo "- Build Rules: $SCRIPT_DIR/AGENTS.md"
echo "- Quick Start: $SCRIPT_DIR/INTEGRATION_BUILD_SYSTEM.md"
echo ""
