#!/bin/bash
# Intelligent Storage Nexus - Startup Script (Gunicorn Edition)

set -e

echo "🚀 Starting Intelligent Storage Nexus..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd ~/Projects/Infrastructure/intelligent-storage

# Detect CPU count for optimal worker count
CPU_COUNT=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
WORKER_COUNT=$((CPU_COUNT * 2 + 1))
if [ $WORKER_COUNT -gt 8 ]; then
    WORKER_COUNT=8  # Cap at 8 workers
fi

echo -e "${BLUE}ℹ️  Detected ${CPU_COUNT} CPUs, using ${WORKER_COUNT} Gunicorn workers${NC}"

# Check if API server is already running
if pgrep -f "gunicorn.*api_server" > /dev/null; then
    echo -e "${YELLOW}⚠️  API server is already running${NC}"
else
    echo -e "${BLUE}▶️  Starting API Server with ${WORKER_COUNT} workers on port 8000...${NC}"
    
    # Gunicorn with Uvicorn workers for async support
    # -w: number of worker processes
    # -k: worker class (UvicornWorker for ASGI/FastAPI)
    # --timeout: worker timeout in seconds
    # --access-logfile: access logs
    # --error-logfile: error logs
    # --capture-output: capture stdout/stderr from workers
    # --enable-stdio-inheritance: allow workers to inherit stdio
    nohup gunicorn api_server:app \
        -w ${WORKER_COUNT} \
        -k uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --timeout 120 \
        --access-logfile api_access.log \
        --error-logfile api_server.log \
        --capture-output \
        --enable-stdio-inheritance \
        > gunicorn.log 2>&1 &
    
    sleep 3
    
    if pgrep -f "gunicorn.*api_server" > /dev/null; then
        echo -e "${GREEN}✅ API Server started successfully with ${WORKER_COUNT} workers${NC}"
        echo -e "${BLUE}   📊 Master PID: $(pgrep -f 'gunicorn.*api_server' | head -1)${NC}"
    else
        echo -e "${YELLOW}❌ Failed to start API Server${NC}"
        echo -e "${YELLOW}   Check gunicorn.log for errors${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}🌐 Access Points:${NC}"
echo -e "   ${BLUE}• Web UI:${NC}      http://localhost:8000"
echo -e "   ${BLUE}• API Docs:${NC}    http://localhost:8000/docs"
echo -e "   ${BLUE}• API Redoc:${NC}   http://localhost:8000/redoc"
echo ""
echo -e "${YELLOW}📊 Features Available:${NC}"
echo "   • Async PostgreSQL with connection pooling"
echo "   • Multi-worker Gunicorn deployment"
echo "   • Semantic Search with AI embeddings"
echo "   • Interactive Knowledge Graph visualization"
echo "   • Tree of Thoughts analysis"
echo "   • Real-time file insights and recommendations"
echo "   • Advanced faceted search and filtering"
echo "   • Live WebSocket updates"
echo ""
echo -e "${GREEN}✨ Open http://localhost:8000 in your browser to get started!${NC}"
echo ""
echo "Press Ctrl+C to stop viewing logs (servers will keep running)"
echo ""

# Show logs
tail -f api_server.log
