# Quick Start Guide

Get Research Swarm running in 5 minutes!

## Prerequisites

- Python 3.11+
- Redis
- OpenAI API key

## Step 1: Installation

```bash
# Clone repository (or use existing)
cd research-swarm-claude

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configuration

```bash
# Copy environment template
cp config/.env.template config/.env

# Edit with your favorite editor
nano config/.env
```

**Required settings:**
```bash
OPENAI_API_KEY=sk-your-key-here
```

**Optional but recommended:**
```bash
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

## Step 3: Start Services

### Option A: Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option B: Manual Setup

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start API
python -m uvicorn api.main:app --reload

# Terminal 3: Start Worker
python orchestrator/worker.py
```

### Option C: Quick Start Script

```bash
./scripts/run_local.sh
```

## Step 4: Test It!

### Submit Your First Idea

```bash
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "Create a simple TODO application with FastAPI backend"
  }'
```

Response:
```json
{
  "idea_id": "abc-123-def",
  "status": "queued",
  "estimated_completion": "2025-11-01T12:30:00",
  "tracking_url": "http://localhost:8000/ideas/abc-123-def"
}
```

### Check Status

```bash
curl http://localhost:8000/api/v1/ideas/abc-123-def/status
```

### View Results

```bash
# Results are saved in:
ls outputs/research-repository/ideas/

# View the summary
cat outputs/research-repository/ideas/2025-11-01-simple-todo-application/SUMMARY.md
```

## Step 5: Explore the API

Visit http://localhost:8000/docs for interactive API documentation.

## Common Issues

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping

# Should return: PONG

# If not, start Redis:
redis-server
```

### OpenAI API Error

```bash
# Verify your API key
echo $OPENAI_API_KEY

# Test it
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Port Already in Use

```bash
# Change the port in config/.env
API_PORT=8001

# Or kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

## Next Steps

1. **iOS Shortcut**: Set up mobile idea capture (see README.md)
2. **Customize**: Adjust settings in `config/.env`
3. **Monitor**: Check metrics at http://localhost:9090/metrics
4. **Scale**: Run multiple workers with `docker-compose up -d --scale worker=3`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Getting Help

- **Documentation**: See README.md
- **Issues**: GitHub Issues
- **Logs**: Check `logs/research-swarm.log`
- **API Docs**: http://localhost:8000/docs

## Example Ideas to Try

```bash
# Simple script
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a weather checker script that emails me the forecast"}'

# Web application
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Build a markdown note-taking web app with Streamlit"}'

# API integration
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a GitHub repository analyzer that shows contribution stats"}'
```

Happy researching! 🚀
