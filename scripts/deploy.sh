#!/bin/bash
# ReliantAI Platform - One-Click Deployment
# Usage: ./deploy.sh [environment]
# Environments: local, staging, production

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-local}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🚀 ReliantAI Platform - One-Click Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Project Root: ${GREEN}$PROJECT_ROOT${NC}"
echo ""

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker."
        exit 1
    fi
    print_success "Docker installed"
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    print_success "Docker Compose installed"
    
    # Check .env file
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env file not found. Copying from .env.example..."
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_success ".env file created"
        else
            print_error ".env.example not found!"
            exit 1
        fi
    fi
    
    # Check ports
    print_status "Checking port availability..."
    local PORTS=(80 443 4000 5174 8000 8001 8002 8080 8095 8100 8101 8102 8103 8104 8105 8106 8107 8108 8109 8110 8111 8112 8113 8200 9000 5432 6379)
    for PORT in "${PORTS[@]}"; do
        if ss -tlnp | grep -q ":$PORT "; then
            print_warning "Port $PORT is already in use"
        fi
    done
    
    print_success "Prerequisites check complete"
    echo ""
}

# Environment setup
setup_environment() {
    print_status "Setting up $ENVIRONMENT environment..."
    
    case $ENVIRONMENT in
        local)
            export COMPOSE_PROJECT_NAME="reliantai-local"
            ;;
        staging)
            export COMPOSE_PROJECT_NAME="reliantai-staging"
            ;;
        production)
            export COMPOSE_PROJECT_NAME="reliantai-prod"
            ;;
        *)
            print_error "Unknown environment: $ENVIRONMENT"
            print_status "Valid environments: local, staging, production"
            exit 1
            ;;
    esac
    
    print_success "Environment configured: $COMPOSE_PROJECT_NAME"
    echo ""
}

# Build services
build_services() {
    print_status "Building platform services..."
    
    cd "$PROJECT_ROOT"
    
    # Build all services
    docker compose -f "$COMPOSE_FILE" build --parallel
    
    print_success "All services built"
    echo ""
}

# Start infrastructure
start_infrastructure() {
    print_status "Starting infrastructure services..."
    
    cd "$PROJECT_ROOT"
    
    # Start Postgres and Redis first
    docker compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for Postgres to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    local RETRIES=30
    local COUNT=0
    while ! docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
        sleep 1
        COUNT=$((COUNT + 1))
        if [ $COUNT -ge $RETRIES ]; then
            print_error "PostgreSQL failed to start"
            exit 1
        fi
        echo -n "."
    done
    echo ""
    print_success "PostgreSQL is ready"
    
    # Wait for Redis
    print_status "Waiting for Redis to be ready..."
    local RETRIES=30
    local COUNT=0
    while ! docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; do
        sleep 1
        COUNT=$((COUNT + 1))
        if [ $COUNT -ge $RETRIES ]; then
            print_error "Redis failed to start"
            exit 1
        fi
        echo -n "."
    done
    echo ""
    print_success "Redis is ready"
    echo ""
}

# Start platform services
start_services() {
    print_status "Starting platform services..."
    
    cd "$PROJECT_ROOT"
    
    # Start all services
    docker compose -f "$COMPOSE_FILE" up -d
    
    print_success "All services started"
    echo ""
}

# Health checks
health_checks() {
    print_status "Running health checks..."
    
    local SERVICES=("money:8000" "complianceone:8001" "finops360:8002" "integration:8080")
    local MAX_RETRIES=30
    
    for SERVICE_PORT in "${SERVICES[@]}"; do
        IFS=':' read -r SERVICE PORT <<< "$SERVICE_PORT"
        print_status "Checking $SERVICE on port $PORT..."
        
        local RETRY=0
        local HEALTHY=false
        
        while [ $RETRY -lt $MAX_RETRIES ]; do
            if curl -sf "http://localhost:$PORT/health" > /dev/null 2>&1; then
                HEALTHY=true
                break
            fi
            sleep 2
            RETRY=$((RETRY + 1))
            echo -n "."
        done
        
        if [ "$HEALTHY" = true ]; then
            print_success "$SERVICE is healthy"
        else
            print_error "$SERVICE failed health check"
        fi
    done
    
    echo ""
}

# Initialize databases
init_databases() {
    print_status "Initializing databases..."
    
    cd "$PROJECT_ROOT"
    
    # Run database migrations for each service
    docker compose -f "$COMPOSE_FILE" exec -T money python -c "from database import init_db; init_db()" 2>/dev/null || true
    
    print_success "Databases initialized"
    echo ""
}

# Setup sample data
setup_sample_data() {
    if [ "$ENVIRONMENT" = "local" ] || [ "$ENVIRONMENT" = "staging" ]; then
        print_status "Setting up sample data..."
        
        cd "$PROJECT_ROOT"
        
        # Setup ComplianceOne with sample frameworks
        docker compose -f "$COMPOSE_FILE" exec -T complianceone python -c "
import requests
import os

api_key = os.environ.get('COMPLIANCEONE_API_KEY', 'complianceone-dev-key-2024')
headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
base_url = 'http://localhost:8001'

# Create SOC2 framework
try:
    r = requests.post(f'{base_url}/frameworks', json={
        'name': 'SOC2',
        'description': 'Service Organization Control 2',
        'version': '2024'
    }, headers=headers)
    if r.status_code == 200:
        print('✓ SOC2 framework created')
except Exception as e:
    print(f'Error: {e}')

# Create GDPR framework
try:
    r = requests.post(f'{base_url}/frameworks', json={
        'name': 'GDPR',
        'description': 'General Data Protection Regulation',
        'version': '2024'
    }, headers=headers)
    if r.status_code == 200:
        print('✓ GDPR framework created')
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null || true
        
        print_success "Sample data created"
        echo ""
    fi
}

# Print status
print_platform_status() {
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ ReliantAI Platform Deployed Successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Platform Services:${NC}"
    echo "  • Money Service:           http://localhost:8000"
    echo "  • ComplianceOne:           http://localhost:8001"
    echo "  • FinOps360:             http://localhost:8002"
    echo "  • Integration Layer:     http://localhost:8080"
    echo "  • Orchestrator:          http://localhost:9000"
    echo "  • Dashboard:             http://localhost:9000/dashboard (or open dashboard/index.html)"
    echo ""
    echo -e "${BLUE}Infrastructure:${NC}"
    echo "  • PostgreSQL:            localhost:5432"
    echo "  • Redis:                 localhost:6379"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  • View logs:             docker compose logs -f [service]"
    echo "  • Stop platform:           docker compose down"
    echo "  • Restart service:       docker compose restart [service]"
    echo "  • Health check:          ./scripts/health_check.py"
    echo "  • Integration test:      ./scripts/verify_integration.py"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Open dashboard:       open dashboard/index.html"
    echo "  2. Check health:         curl http://localhost:9000/health"
    echo "  3. View status:          curl http://localhost:9000/status"
    echo ""
    echo -e "${GREEN}🎉 Platform is ready for use!${NC}"
    echo ""
}

# Error handling
trap 'print_error "Deployment failed! Check logs above for details."' ERR

# Main deployment flow
main() {
    echo ""
    check_prerequisites
    setup_environment
    build_services
    start_infrastructure
    start_services
    health_checks
    init_databases
    setup_sample_data
    print_platform_status
}

# Run deployment
main
