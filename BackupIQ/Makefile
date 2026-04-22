# Enterprise Backup System Makefile
# FAANG-grade build and test automation

.PHONY: help install dev-install test test-unit test-integration test-e2e test-performance test-security lint format check clean build deploy docker-build docker-run k8s-deploy

# Configuration
PYTHON := python3
PIP := pip3
PROJECT_NAME := intelligent-backup-enterprise
VERSION := 1.0.0
REGISTRY := your-registry.com

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
help:
	@echo "$(BLUE)Intelligent Backup Enterprise - Build System$(NC)"
	@echo ""
	@echo "$(YELLOW)Development Commands:$(NC)"
	@echo "  make install         Install production dependencies"
	@echo "  make dev-install     Install development dependencies"
	@echo "  make test           Run all tests"
	@echo "  make lint           Run linting checks"
	@echo "  make format         Auto-format code"
	@echo "  make check          Run all quality checks"
	@echo ""
	@echo "$(YELLOW)Test Commands:$(NC)"
	@echo "  make test-unit      Run unit tests with coverage"
	@echo "  make test-integration  Run integration tests"
	@echo "  make test-e2e       Run end-to-end tests"
	@echo "  make test-performance  Run performance benchmarks"
	@echo "  make test-security  Run security scans"
	@echo ""
	@echo "$(YELLOW)Build & Deploy:$(NC)"
	@echo "  make build          Build Python package"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo "  make k8s-deploy     Deploy to Kubernetes"
	@echo ""
	@echo "$(YELLOW)Utility Commands:$(NC)"
	@echo "  make clean          Clean build artifacts"
	@echo "  make deps-update    Update dependencies"

# Installation
install:
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt

dev-install: install
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	pre-commit install

# Testing
test: test-unit test-integration test-security
	@echo "$(GREEN)All tests completed!$(NC)"

test-unit:
	@echo "$(GREEN)Running unit tests with coverage...$(NC)"
	$(PYTHON) -m pytest tests/unit/ \
		--cov=src/ \
		--cov-report=html:htmlcov \
		--cov-report=term-missing \
		--cov-fail-under=95 \
		--json-report \
		--json-report-file=test-results/unit-results.json \
		-v

test-integration:
	@echo "$(GREEN)Running integration tests...$(NC)"
	$(PYTHON) -m pytest tests/integration/ \
		--json-report \
		--json-report-file=test-results/integration-results.json \
		-v -s

test-e2e:
	@echo "$(GREEN)Running end-to-end tests...$(NC)"
	$(PYTHON) -m pytest tests/e2e/ \
		--json-report \
		--json-report-file=test-results/e2e-results.json \
		-v -s

test-performance:
	@echo "$(GREEN)Running performance benchmarks...$(NC)"
	$(PYTHON) -m pytest tests/performance/ \
		--benchmark-json=test-results/benchmark-results.json \
		-v

test-security:
	@echo "$(GREEN)Running security scans...$(NC)"
	@mkdir -p test-results
	bandit -r src/ -f json -o test-results/bandit-results.json || true
	safety check --json > test-results/safety-results.json || true
	@echo "$(YELLOW)Security scan results saved to test-results/$(NC)"

test-all:
	@echo "$(GREEN)Running comprehensive test suite...$(NC)"
	$(PYTHON) tests/test_runner.py

# Code Quality
lint:
	@echo "$(GREEN)Running linting checks...$(NC)"
	flake8 src/ tests/ --max-line-length=100
	pylint src/ --rcfile=.pylintrc || true
	mypy src/ --config-file=mypy.ini

format:
	@echo "$(GREEN)Auto-formatting code...$(NC)"
	black src/ tests/ --line-length=100
	isort src/ tests/ --profile=black

check: lint format test-security
	@echo "$(GREEN)All quality checks passed!$(NC)"

# Build
build: clean
	@echo "$(GREEN)Building Python package...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel

docker-build:
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(PROJECT_NAME):$(VERSION) -f deployment/docker/Dockerfile .
	docker build -t $(PROJECT_NAME):latest -f deployment/docker/Dockerfile .

docker-run:
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run -d \
		--name $(PROJECT_NAME) \
		-p 8080:8080 \
		-p 9090:9090 \
		-v $(PWD)/config:/home/appuser/app/config:ro \
		$(PROJECT_NAME):latest

docker-compose-up:
	@echo "$(GREEN)Starting Docker Compose stack...$(NC)"
	cd deployment/docker && docker-compose up -d

docker-compose-down:
	@echo "$(YELLOW)Stopping Docker Compose stack...$(NC)"
	cd deployment/docker && docker-compose down

# Kubernetes
k8s-deploy:
	@echo "$(GREEN)Deploying to Kubernetes...$(NC)"
	kubectl apply -f deployment/k8s/

k8s-undeploy:
	@echo "$(YELLOW)Removing from Kubernetes...$(NC)"
	kubectl delete -f deployment/k8s/

# Development Environment
dev-setup: dev-install
	@echo "$(GREEN)Setting up development environment...$(NC)"
	mkdir -p logs test-results htmlcov
	@echo "$(GREEN)Development environment ready!$(NC)"

dev-run:
	@echo "$(GREEN)Running development server...$(NC)"
	ENVIRONMENT=development $(PYTHON) -m src.core.backup_orchestrator

# Dependency Management
deps-update:
	@echo "$(GREEN)Updating dependencies...$(NC)"
	$(PIP) list --outdated
	@echo "$(YELLOW)Review outdated packages and update requirements.txt manually$(NC)"

deps-check:
	@echo "$(GREEN)Checking dependency security...$(NC)"
	safety check

# Cleanup
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-all: clean
	@echo "$(YELLOW)Deep cleaning...$(NC)"
	rm -rf test-results/
	docker system prune -f || true

# Release
release-patch:
	@echo "$(GREEN)Creating patch release...$(NC)"
	bump2version patch

release-minor:
	@echo "$(GREEN)Creating minor release...$(NC)"
	bump2version minor

release-major:
	@echo "$(GREEN)Creating major release...$(NC)"
	bump2version major

# Documentation
docs-build:
	@echo "$(GREEN)Building documentation...$(NC)"
	cd docs && make html

docs-serve:
	@echo "$(GREEN)Serving documentation...$(NC)"
	cd docs/_build/html && $(PYTHON) -m http.server 8000

# Monitoring
monitor-start:
	@echo "$(GREEN)Starting monitoring stack...$(NC)"
	cd monitoring && docker-compose up -d

monitor-stop:
	@echo "$(YELLOW)Stopping monitoring stack...$(NC)"
	cd monitoring && docker-compose down

# CI/CD Integration
ci-test: dev-install test-all
	@echo "$(GREEN)CI test pipeline completed$(NC)"

ci-build: clean build docker-build
	@echo "$(GREEN)CI build pipeline completed$(NC)"

# Health checks
health:
	@echo "$(GREEN)Checking system health...$(NC)"
	@curl -f http://localhost:8080/health 2>/dev/null || echo "$(RED)Health check failed$(NC)"

metrics:
	@echo "$(GREEN)Fetching metrics...$(NC)"
	@curl -s http://localhost:9090/metrics | head -20 || echo "$(RED)Metrics endpoint unavailable$(NC)"

# Git hooks
pre-commit: format lint test-unit
	@echo "$(GREEN)Pre-commit checks passed$(NC)"

# Performance monitoring
profile:
	@echo "$(GREEN)Running performance profiler...$(NC)"
	$(PYTHON) -m cProfile -o profile.stats -m src.core.backup_orchestrator
	@echo "$(YELLOW)Profile saved to profile.stats$(NC)"

# Debugging
debug:
	@echo "$(GREEN)Starting debug session...$(NC)"
	$(PYTHON) -m pdb -m src.core.backup_orchestrator

# Load testing
load-test:
	@echo "$(GREEN)Running load tests...$(NC)"
	locust -f tests/load/locustfile.py --host=http://localhost:8080

# Database operations
db-migrate:
	@echo "$(GREEN)Running database migrations...$(NC)"
	alembic upgrade head

db-seed:
	@echo "$(GREEN)Seeding database...$(NC)"
	$(PYTHON) scripts/seed_database.py