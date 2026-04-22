# Makefile for the Citadel Project

.PHONY: all build up down logs test clean install-hooks help

# Default command
help:
	@echo "Citadel Project Makefile"
	@echo "------------------------"
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  all          - Build and start all services."
	@echo "  build        - Build or rebuild all Docker services."
	@echo "  up           - Start all services in detached mode."
	@echo "  down         - Stop and remove all services."
	@echo "  logs         - Follow logs from all services."
	@echo "  test         - Run all tests using pytest."
	@echo "  clean        - Remove Docker volumes and built artifacts."
	@echo "  install-dev  - Install local development dependencies and pre-commit hooks."
	@echo "  format       - Run black and isort to format the code."

all: build up

build:
	@echo "Building Docker images..."
	docker-compose -f compose.yaml build

up:
	@echo "Starting services..."
	docker-compose -f compose.yaml up -d

down:
	@echo "Stopping and removing services..."
	docker-compose -f compose.yaml down

logs:
	@echo "Following logs..."
	docker-compose -f compose.yaml logs -f

test:
	@echo "Running tests..."
	python3 -m pytest tests/

clean: down
	@echo "Cleaning up Docker volumes..."
	docker-compose -f compose.yaml down -v
	@echo "Cleaning Python cache..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +

install-dev:
	@echo "Installing development dependencies..."
	pip install -r local_agent/requirements.txt
	pip install black isort flake8 pytest pytest-asyncio pre-commit
	@echo "Installing pre-commit hooks..."
	pre-commit install

format:
	@echo "Formatting code with black and isort..."
	black .
	isort .
