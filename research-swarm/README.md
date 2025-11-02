# Research Automation Swarm

A personal AI research swarm that instantly captures "flood thoughts" and autonomously produces actionable research or working prototypes through an orchestrated multi-agent system.

## Overview

The Research Swarm is an automated pipeline that:
- Captures ideas through quick mobile interface
- Deploys intelligent agents for research and analysis
- Makes autonomous decisions about implementation feasibility
- Builds functional prototypes using TDD methodology
- Delivers tested code or comprehensive research reports

## Architecture

The system consists of several main components:

- **API Gateway**: Handles idea submission and status checking via FastAPI
- **Orchestrator**: Manages the research workflow using LangGraph
- **Agents**: Specialized AI agents for planning, research, building, and testing
- **Repository Manager**: Handles git repository operations for output storage
- **Queue System**: Uses Redis to manage idea processing

## Components

### Agents
- **Planner Agent**: Analyzes ideas and creates initial plans
- **Research Agents**: Four specialized agents (API, Code, Papers, Tools) for parallel research
- **Builder Agent**: Generates code using TDD approach
- **Tester Agent**: Runs unit, integration, and E2E tests

### Infrastructure
- Redis for queue management
- Git for output repository management
- Prometheus for metrics collection
- Docker and Kubernetes for containerization

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r pyproject.toml` or `uv pip install -r pyproject.toml`
3. Set up virtual environment (recommended):
   - Option A: `python3 -m venv venv && source venv/bin/activate && pip install -r pyproject.toml`
   - Option B: Using uv: `uv venv && source .venv/bin/activate && uv pip install -r pyproject.toml`
4. Set up environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your-openai-key
   SERPAPI_API_KEY=your-serpapi-key (optional)
   TAILSCALE_AUTH_KEY=your-tailscale-key
   DB_PASSWORD=your-db-password
   EMAIL_FROM=your-email
   EMAIL_TO=recipient-email
   REPO_PATH=/path/to/output/repo
   ```
5. Run Redis: `docker run -p 6379:6379 redis:7-alpine`
6. Start the API: `uvicorn api.main:app --reload`
7. Start the worker: `python orchestrator/worker.py`

## Testing

The project includes comprehensive tests for all components:

- **Unit Tests**: Individual component testing in the `tests/` directory
- **Mock-based Tests**: Tests that mock external dependencies like LLMs
- **Integration Points**: Testing of all major workflow components

To run tests (after setting up the virtual environment):
```bash
pytest tests/ -v
```

The test suite includes:
- `test_planner.py`: Tests for the idea planning component
- `test_researcher.py`: Tests for the research swarm agents
- `test_builder.py`: Tests for the code generation component  
- `test_tester.py`: Tests for the testing and validation component
- `test_workflow.py`: Tests for the LangGraph workflow orchestrator
- `test_repository.py`: Tests for the Git repository management
- `test_api.py`: Tests for the API gateway functionality

All tests include comprehensive error handling and edge case coverage.

## Usage

Submit an idea via the API:
```bash
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a weather app that shows forecasts"}'
```

Check the status of your idea:
```bash
curl http://localhost:8000/api/v1/ideas/{idea_id}/status
```

## iOS Shortcuts Integration

The system can be integrated with iOS Shortcuts for quick idea capture. The shortcut sends a POST request to the API endpoint with the idea text.

## Output Repository Structure

The system generates output in a git repository with the following structure:

```
/research-repository/
├── README.md
├── ideas/
│   └── 2025-11-01-idea-title/
│       ├── metadata.json
│       ├── research/
│       │   ├── README.md
│       │   ├── feasibility.md
│       │   └── references.md
│       ├── plan/
│       │   ├── architecture.md
│       │   └── tasks.json
│       ├── implementation/
│       │   ├── src/
│       │   ├── tests/
│       │   └── README.md
│       └── results/
│           ├── test-report.html
│           └── summary.md
```