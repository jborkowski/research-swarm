# Research Swarm Setup Guide

Complete guide to setting up and running your Research Automation Swarm system.

## Prerequisites

### Required Software
- Python 3.11 or higher
- Redis (for job queue)
- Git (for repository management)
- OpenAI API key (for LLM capabilities)

### Optional Software
- Docker & Docker Compose (for containerized deployment)
- PostgreSQL (for production metadata storage)
- Tailscale (for secure remote access)

## Quick Start (Local Development)

### 1. Clone and Setup Python Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd research-swarm-claude

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the template and configure your API keys:

```bash
# Copy environment template
cp config/.env.template config/.env

# Edit config/.env with your settings
```

Required variables:
```bash
# API Keys
OPENAI_API_KEY=sk-your-openai-key-here

# Optional API Keys
SERPAPI_API_KEY=your-serpapi-key  # For web search
ANTHROPIC_API_KEY=your-anthropic-key  # For Claude models

# Infrastructure
REDIS_URL=redis://localhost:6379

# Repository Path
REPOSITORY_PATH=./outputs/research-repository

# Email Notifications (Optional)
EMAIL_FROM=your-email@example.com
EMAIL_TO=your-email@example.com
EMAIL_PASSWORD=your-app-password
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# Discord Notifications (Optional)
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

### 3. Start Redis

**Option A: Using Homebrew (macOS)**
```bash
brew services start redis
```

**Option B: Using Docker**
```bash
docker run -d -p 6379:6379 --name research-redis redis:7-alpine
```

**Option C: Direct Command**
```bash
redis-server --daemonize yes
```

### 4. Initialize Output Repository

```bash
# Create output directory
mkdir -p outputs/research-repository/ideas

# Initialize Git repository for outputs
cd outputs/research-repository
git init
git config user.name "Research Swarm"
git config user.email "swarm@localhost"
cd ../..
```

### 5. Start the API Server

In terminal window #1:
```bash
source venv/bin/activate
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 6. Start the Worker

In terminal window #2:
```bash
source venv/bin/activate
python orchestrator/worker.py
```

### 7. Test the System

Submit a test idea:
```bash
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "Create a simple weather app that shows current temperature",
    "priority": "medium"
  }'
```

You should receive a response with an `idea_id`. Check the status:
```bash
curl http://localhost:8000/api/v1/ideas/<idea_id>/status
```

Monitor the worker logs to see the processing pipeline in action.

## Component Overview

### API Server (`api/main.py`)
- FastAPI application
- Endpoints for submitting ideas and checking status
- Queues jobs in Redis
- Port: 8000

### Worker (`orchestrator/worker.py`)
- Background job processor
- Pulls jobs from Redis queue
- Orchestrates the workflow
- Runs continuously

### Orchestrator (`orchestrator/workflow.py`)
- LangGraph-based workflow engine
- Manages state transitions
- Coordinates agents

### Agents
- **PlannerAgent** (`agents/planner.py`): Analyzes ideas and creates plans
- **ResearchSwarm** (`agents/researcher.py`): Parallel research across domains
- **BuilderAgent** (`agents/builder.py`): Generates code with TDD
- **TesterAgent** (`agents/tester.py`): Runs tests and validates implementation

### Utilities
- **RepositoryManager** (`utils/repository.py`): Git-based output management
- **Notifications** (`utils/notifications.py`): Email/Discord alerts
- **Metrics** (`utils/metrics.py`): Prometheus metrics collection

## Output Structure

All results are stored in the Git repository:

```
outputs/research-repository/
└── ideas/
    └── 2025-11-01-weather-app/
        ├── metadata.json              # Job metadata
        ├── research/
        │   ├── README.md              # Research summary
        │   ├── feasibility.md         # Analysis
        │   └── references.md          # Sources
        ├── plan/
        │   └── architecture.md        # Technical plan
        ├── implementation/            # Generated code
        │   ├── src/
        │   ├── tests/
        │   └── README.md
        ├── results/
        │   ├── test-report.md
        │   └── coverage.json
        └── SUMMARY.md                 # Final summary
```

## Docker Deployment

### Build Images

```bash
# Build API image
docker build -t research-swarm-api:latest -f Dockerfile.api .

# Build Worker image
docker build -t research-swarm-worker:latest -f Dockerfile.worker .
```

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## iOS Shortcut Setup

### 1. Install Shortcut

On your iOS device:
1. Open Shortcuts app
2. Create new shortcut
3. Add "Ask for Input" action
   - Prompt: "What's your idea?"
4. Add "Get Contents of URL" action
   - URL: `http://your-server:8000/api/v1/ideas`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Request Body: JSON
     ```json
     {
       "idea": "<Input>",
       "priority": "medium"
     }
     ```
5. Add "Show Notification" action
   - Title: "Idea Submitted!"
   - Body: "Processing your research request..."

### 2. With Tailscale (Recommended)

For secure remote access:

```bash
# Install Tailscale on server
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Get Tailscale IP
tailscale ip -4
```

Update shortcut URL to use Tailscale IP: `http://100.x.x.x:8000/api/v1/ideas`

### 3. Add Trigger

Configure shortcut trigger:
- Back Tap (2 or 3 taps)
- Widget on home screen
- Siri phrase: "Research this idea"

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Queue Statistics

```bash
curl http://localhost:8000/api/v1/queue/stats
```

### Prometheus Metrics

Available at: `http://localhost:9090/metrics`

Metrics include:
- `ideas_processed_total` - Total ideas processed
- `ideas_failed_total` - Total failures
- `processing_time_seconds` - Processing duration histogram
- `queue_depth` - Current queue size
- `active_pods` - Active agent pods

### Logs

Logs are written to:
- Console (stdout)
- `logs/research-swarm.log`

Log format: JSON structured logs

## Troubleshooting

### Redis Connection Failed

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check Redis connection
redis-cli -u redis://localhost:6379 ping
```

### API Not Responding

```bash
# Check if API is running
ps aux | grep uvicorn

# Check logs
tail -f logs/research-swarm.log

# Verify port is available
lsof -i :8000
```

### Worker Not Processing Jobs

```bash
# Check worker logs
# Look for connection errors or exceptions

# Verify queue has jobs
redis-cli
> LLEN idea_queue

# Check job status
> HGETALL idea:<idea-id>
```

### OpenAI API Errors

Common issues:
- Invalid API key: Check `OPENAI_API_KEY` in `.env`
- Rate limits: Reduce concurrency or upgrade plan
- Quota exceeded: Check OpenAI dashboard

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify Python path
echo $PYTHONPATH
# Should include /app or project root
```

## Performance Tuning

### Adjust Timeouts

In `config/settings.py`:
```python
research_timeout: int = 900  # 15 minutes
build_timeout: int = 1800    # 30 minutes
max_iterations: int = 10      # Max retry attempts
```

### Model Selection

For faster/cheaper processing:
```python
default_model: str = "gpt-3.5-turbo"  # Instead of gpt-4
temperature: float = 0.1
```

### Concurrency

Edit `docker-compose.yml` to run multiple workers:
```yaml
worker:
  deploy:
    replicas: 3  # Run 3 worker instances
```

## Production Deployment

### Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Enable HTTPS with reverse proxy (nginx/Caddy)
- [ ] Configure firewall rules
- [ ] Set up Tailscale ACLs
- [ ] Use secrets manager (HashiCorp Vault)
- [ ] Enable Redis authentication
- [ ] Review API rate limiting
- [ ] Set up monitoring alerts

### Recommended Stack

```
[iOS Device]
    ↓ Tailscale VPN
[Nginx Reverse Proxy with SSL]
    ↓
[API Server (uvicorn)]
    ↓
[Redis Queue]
    ↓
[Worker Processes]
    ↓
[Git Repository]
```

### Backup Strategy

```bash
# Backup outputs repository
tar -czf backup-$(date +%Y%m%d).tar.gz outputs/research-repository/

# Backup Redis data
redis-cli SAVE
cp /var/lib/redis/dump.rdb backup/

# Automate with cron
0 2 * * * /path/to/backup-script.sh
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_workflow.py -v
```

### Code Quality

```bash
# Format code
black .

# Lint code
autopep8 --in-place --recursive .
```

## Support

For issues and questions:
- Check logs in `logs/research-swarm.log`
- Review queue status with Redis CLI
- Check agent implementations in `agents/` directory
- Review workflow logic in `orchestrator/workflow.py`

## Next Steps

1. Submit test ideas and review outputs
2. Configure email/Discord notifications
3. Set up iOS Shortcut for mobile access
4. Customize agent prompts for your use case
5. Add custom research agents
6. Deploy to production environment

Happy researching! 🔬
