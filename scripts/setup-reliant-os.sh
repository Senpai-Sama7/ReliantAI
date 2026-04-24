#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Reliant JIT OS - Setup Script                    ║"
echo "║     Zero-Configuration Autonomous Platform Setup             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build and start the Reliant OS services
echo "🔨 Building Reliant OS services..."

cd "$(dirname "$0")/.."

# Build backend
echo "  📦 Building backend..."
docker compose build reliant-os-backend > /dev/null 2>&1

# Build frontend
echo "  🎨 Building frontend..."
docker compose build reliant-os-frontend > /dev/null 2>&1

# Start services
echo ""
echo "🚀 Starting Reliant OS..."
docker compose up -d reliant-os-backend reliant-os-frontend

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
if curl -s http://localhost:8004/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend may still be starting..."
fi

if curl -s http://localhost:8085/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              🎉 Reliant JIT OS is Ready!                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📱 Access the interface: http://localhost:8085"
echo "🔌 Backend API: http://localhost:8004"
echo ""
echo "📝 Next Steps:"
echo "   1. Open http://localhost:8085 in your browser"
echo "   2. Complete the secure setup wizard"
echo "   3. Start using your autonomous platform!"
echo ""
echo "💡 The AI will guide you through configuration."
echo "   No manual .env editing required!"
echo ""
