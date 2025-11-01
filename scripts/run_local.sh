#!/bin/bash
# Quick start script for local development

set -e

echo "🚀 Starting Research Swarm locally..."

if [ ! -f "config/.env" ]; then
    echo "⚠️  config/.env not found. Creating from template..."
    cp config/.env.template config/.env
    echo "📝 Please edit config/.env with your API keys"
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo "🔧 Initializing..."
python scripts/init_db.py

if [ $? -ne 0 ]; then
    echo "❌ Initialization failed"
    exit 1
fi

echo ""
echo "Starting services..."
echo "  - Redis: redis-server"
echo "  - API: http://localhost:8000"
echo "  - Worker: Background process"
echo ""

trap 'kill $(jobs -p) 2>/dev/null' EXIT

redis-server --daemonize yes

echo "Starting API server..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

sleep 2

echo "Starting worker..."
python orchestrator/worker.py &
WORKER_PID=$!

echo ""
echo "✅ All services started!"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

wait
