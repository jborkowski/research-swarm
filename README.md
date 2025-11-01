# Research Automation Swarm System

A personal AI research swarm that instantly captures "flood thoughts" and autonomously produces actionable research or working prototypes through an orchestrated multi-agent system.

## Overview

The Research Automation Swarm System is an AI-powered platform that:
- Captures ideas through iOS Shortcuts + Tailscale VPN
- Processes ideas through an orchestrated multi-agent system using LangGraph
- Automatically generates research, feasibility analysis, and working prototypes
- Uses TDD methodology for code generation
- Organizes output in Git repositories with comprehensive documentation

## Features

- **One-touch idea capture** with <10 second latency
- **Automated research** with <15 minute timeout
- **TDD-based prototype generation** with <30 minute timeout
- **Fail-fast mechanism** with 10 iteration limit
- **Comprehensive test coverage** (>70%)
- **Git-based output organization**
- **Human-in-the-loop decision points**

## Architecture

```
Input Layer (iOS Shortcuts + Tailscale VPN)
    ↓
Processing Layer (Redis Queue + LangGraph Orchestration)
    ↓
Execution Layer (Specialized Agent Pods)
    ↓
Storage Layer (Git Repository + PostgreSQL metadata)
    ↓
Notification Layer (Email/Discord notifications)
```

## Components

### 1. API Gateway
- FastAPI-based REST API for idea submission
- Redis queue management
- Status tracking endpoints

### 2. Orchestration Engine
- LangGraph workflow orchestration
- State management
- Conditional routing logic

### 3. Agent System
- **Planner Agent**: Complexity analysis and task decomposition
- **Research Swarm**: Parallel research execution (API, code, papers, tools)
- **Builder Agent**: TDD-based code generation
- **Tester Agent**: Unit, integration, and E2E testing

### 4. Repository Manager
- Git-based output organization
- Automated commit and push
- Comprehensive documentation generation

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Git

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd research-swarm
```

2. **Create environment file:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start the system:**
```bash
docker-compose up -d
```

4. **Verify the system is running:**
```bash
curl http://localhost:8000/docs
```

### Usage

1. **Submit an idea:**
```bash
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a weather notification app"}'
```

2. **Check idea status:**
```bash
curl http://localhost:8000/api/v1/ideas/{idea_id}/status
```

3. **View generated output:**
```bash
ls ./research-output/ideas/
```

## Development

### Local Development Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start Redis:**
```bash
docker-compose up -d redis
```

4. **Start API server:**
```bash
uvicorn api.main:app --reload
```

5. **Start worker:**
```bash
python -m orchestrator.worker
```

### Testing

```bash
# Run unit tests
pytest tests/

# Run specific test
pytest tests/test_system.py::test_planner_agent
```

## Configuration

The system can be configured through environment variables:

- `OPENAI_API_KEY`: OpenAI API key for LLM features
- `REDIS_URL`: Redis connection string
- `REPO_PATH`: Path to output repository
- `MAX_ITERATIONS`: Maximum build iterations (default: 10)

## Project Structure

```
research-swarm/
├── agents/          # AI agent implementations
├── api/             # REST API gateway
├── config/          # Configuration management
├── orchestrator/    # Workflow orchestration
├── utils/           # Utility functions
├── tests/           # Test suite
├── research-output/ # Generated research output
└── docs/           # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LangChain for AI orchestration
- LangGraph for workflow management
- FastAPI for the REST API
- Redis for queue management