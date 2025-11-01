# Research Swarm

An AI-powered research automation system that transforms ideas into working prototypes through autonomous multi-agent orchestration.

## Overview

Research Swarm captures "flood thoughts" and autonomously produces actionable research or working prototypes through an orchestrated multi-agent system powered by LangGraph and LangChain.

### Key Features

- **Instant Idea Capture**: Submit ideas via API or iOS Shortcuts
- **Autonomous Research**: Parallel research agents investigate multiple domains
- **TDD Implementation**: Generates working code with tests
- **Smart Orchestration**: LangGraph-powered workflow with conditional branching
- **Git-Based Output**: All results versioned in structured repository
- **Notifications**: Email and Discord alerts on completion

### Success Metrics

- Idea capture time: < 10 seconds
- Research completion: < 15 minutes
- POC generation: < 30 minutes
- Test coverage: > 70%
- Iteration limit: 10 attempts before fail-fast

## Architecture

```
┌─────────────┐
│ iOS Shortcut│
└──────┬──────┘
       │
       v
┌─────────────┐     ┌──────────┐
│  API Gateway│────>│  Redis   │
└─────────────┘     └────┬─────┘
                         │
                         v
                  ┌──────────────┐
                  │ Orchestrator │
                  │  (LangGraph) │
                  └──────┬───────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        v                v                v
   ┌─────────┐    ┌──────────┐    ┌─────────┐
   │ Planner │    │ Research │    │ Builder │
   │  Agent  │    │  Swarm   │    │  Agent  │
   └─────────┘    └──────────┘    └─────────┘
                                        │
                                        v
                                  ┌──────────┐
                                  │  Tester  │
                                  │  Agent   │
                                  └────┬─────┘
                                       │
                                       v
                                  ┌──────────┐
                                  │   Git    │
                                  │Repository│
                                  └──────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Redis
- Docker (optional)
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/research-swarm.git
cd research-swarm
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp config/.env.template config/.env
# Edit config/.env with your API keys
```

4. **Start services**

Using Docker:
```bash
docker-compose up -d
```

Or manually:
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 3: Start Worker
python orchestrator/worker.py
```

### Submit Your First Idea

```bash
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "Create a simple TODO app with FastAPI and React",
    "priority": "medium"
  }'
```

Check status:
```bash
curl http://localhost:8000/api/v1/ideas/{idea_id}/status
```

## Configuration

### Environment Variables

```bash
# API Keys
OPENAI_API_KEY=sk-your-key-here
SERPAPI_API_KEY=your-key-here  # Optional
ANTHROPIC_API_KEY=your-key-here  # Optional

# Infrastructure
REDIS_URL=redis://localhost:6379
REPO_PATH=./outputs/research-repository

# Execution Limits
MAX_ITERATIONS=10
RESEARCH_TIMEOUT=900  # 15 minutes
BUILD_TIMEOUT=1800    # 30 minutes

# Notifications
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...

# LLM Configuration
DEFAULT_MODEL=gpt-4
TEMPERATURE=0.1
```

## Workflow Phases

### Phase 1: Zero-Shot Planning (0-5 min)
- Analyzes idea complexity
- Determines research needs
- Creates initial task outline

### Phase 2: Research Swarm (0-15 min)
- **API Scout**: Finds relevant APIs
- **Code Hunter**: Searches implementations
- **Tool Finder**: Identifies frameworks
- **Compliance Checker**: Reviews requirements

### Phase 3: Knowledge Synthesis (5-10 min)
- Aggregates research findings
- Identifies conflicts/gaps
- Creates detailed specification

### Phase 4: TDD Implementation (10-30 min)
- Writes tests first (RED)
- Implements code (GREEN)
- Refactors (REFACTOR)
- Max 10 iterations

### Phase 5: Testing & Validation (5-10 min)
- Unit tests (70%+ coverage target)
- Integration tests
- E2E tests (if applicable)

### Phase 6: Reporting
- Generates comprehensive documentation
- Commits to Git repository
- Sends notifications

## API Reference

### Submit Idea
```http
POST /api/v1/ideas
Content-Type: application/json

{
  "idea": "Your idea here",
  "priority": "medium",
  "context": "Optional context",
  "constraints": {}
}
```

### Get Status
```http
GET /api/v1/ideas/{idea_id}/status
```

### Cancel Idea
```http
DELETE /api/v1/ideas/{idea_id}
```

### Queue Stats
```http
GET /api/v1/queue/stats
```

## Output Repository Structure

```
outputs/research-repository/
├── ideas/
│   └── 2025-11-01-todo-app/
│       ├── metadata.json
│       ├── research/
│       │   ├── README.md
│       │   ├── feasibility.md
│       │   └── research_data.json
│       ├── plan/
│       │   ├── plan.json
│       │   └── implementation_plan.md
│       ├── implementation/
│       │   ├── src/
│       │   ├── tests/
│       │   ├── requirements.txt
│       │   └── README.md
│       ├── results/
│       │   ├── test-report.md
│       │   └── test-results.json
│       └── SUMMARY.md
```

## iOS Shortcut Setup

1. Install Tailscale on your iOS device and server
2. Create new Shortcut with these actions:
   - Text Input: "What's your idea?"
   - Get Network: Tailscale
   - POST to `https://{tailscale-ip}:8000/api/v1/ideas`
   - Show Notification with tracking URL

3. Add triggers:
   - Back tap (2 taps)
   - Widget
   - Siri phrase: "Research idea"

## Development

### Run Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Code Formatting
```bash
black .
```

### Type Checking
```bash
mypy .
```

## Monitoring

### Prometheus Metrics
Available at `http://localhost:9090/metrics`

Metrics include:
- `ideas_processed_total` - Total ideas processed
- `ideas_failed_total` - Failed ideas by phase
- `processing_time_seconds` - Processing duration histogram
- `queue_depth` - Current queue size
- `phase_duration_seconds` - Phase-specific durations

### Logs
- Console: Structured JSON logs
- File: `logs/research-swarm.log`

## Troubleshooting

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping

# Verify connection string
echo $REDIS_URL
```

### API Key Errors
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check rate limits
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Worker Not Processing
```bash
# Check queue
redis-cli llen idea_queue

# Check worker logs
docker logs research-swarm-worker
```

### Tests Failing
```bash
# Install test dependencies
pip install pytest-asyncio pytest-cov

# Run with verbose output
pytest -v
```

## Deployment

### Docker Deployment
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale worker=3
```

### Production Considerations

1. **Security**
   - Use Tailscale VPN for secure access
   - Store secrets in environment variables
   - Enable HTTPS with valid certificates

2. **Reliability**
   - Set up Redis persistence
   - Configure automatic restarts
   - Implement health checks

3. **Monitoring**
   - Export metrics to Prometheus
   - Set up alerting for failures
   - Monitor queue depth

4. **Scaling**
   - Run multiple worker instances
   - Use managed Redis (AWS ElastiCache, etc.)
   - Consider cloud deployment (RunPod, GCP, AWS)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

- Issues: GitHub Issues
- Email: support@example.com
- Docs: See `docs/` directory

## Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Powered by [LangGraph](https://github.com/langchain-ai/langgraph)
- Inspired by [MetaGPT](https://github.com/geekan/MetaGPT)

---

Made with by the Research Automation Team
