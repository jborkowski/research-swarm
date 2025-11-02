#!/bin/bash

# Research Swarm Local Development Environment
# This script sets up and runs the full Research Swarm environment locally

set -e

echo "🚀 Starting Research Swarm Local Environment"
echo "=============================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with your API keys."
    echo "   See .env.example for the required variables."
    exit 1
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p outputs logs monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards

# Start the environment
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "⚠️  API might not be ready yet"
fi

echo ""
echo "🎉 Environment is running!"
echo ""
echo "📊 Access URLs:"
echo "   API:        http://localhost:8000"
echo "   API Docs:   http://localhost:8000/docs"
echo "   Grafana:    http://localhost:3000 (admin/admin)"
echo "   Prometheus: http://localhost:9090"
echo "   Loki:       http://localhost:3100"
echo ""
echo "🧪 Test the API:"
echo "   curl -X POST http://localhost:8000/api/v1/ideas \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"idea\": \"Create a simple calculator app\"}'"
echo ""
echo "🛑 To stop: docker-compose down"
echo "🧹 To cleanup: docker-compose down -v"
