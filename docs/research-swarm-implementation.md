# Technical Implementation Guide
## Research Automation Swarm System

**Version:** 1.0  
**Date:** November 1, 2025  
**Purpose:** Step-by-step implementation guide with code examples

---

## 1. Quick Start Setup

### 1.1 Prerequisites

```bash
# System Requirements
- macOS with OrbStack OR Linux with Docker
- Python 3.11+
- Node.js 20+
- Redis
- Git
- Tailscale account

# Install OrbStack (macOS)
brew install orbstack

# Install Docker (Linux)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
```

### 1.2 Project Structure

```bash
# Create project structure
mkdir -p research-swarm/{agents,api,config,orchestrator,outputs,tests}
cd research-swarm

# Initialize Git repository
git init
git remote add origin <your-repo-url>

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install base dependencies
pip install langchain langraph openai redis bullmq pydantic fastapi uvicorn
```

---

## 2. Core Components Implementation

### 2.1 Configuration Management

```python
# config/settings.py
from pydantic import BaseSettings, Field
from typing import Optional
import os

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    serpapi_api_key: Optional[str] = Field(None, env="SERPAPI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Infrastructure
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    tailscale_auth_key: str = Field(..., env="TAILSCALE_AUTH_KEY")
    repository_path: str = Field("/home/user/research-output", env="REPO_PATH")
    
    # Execution Limits
    max_iterations: int = Field(10, env="MAX_ITERATIONS")
    research_timeout: int = Field(900, env="RESEARCH_TIMEOUT")  # 15 minutes
    build_timeout: int = Field(1800, env="BUILD_TIMEOUT")  # 30 minutes
    
    # Notification
    email_smtp_server: str = Field("smtp.gmail.com", env="SMTP_SERVER")
    email_from: str = Field(..., env="EMAIL_FROM")
    email_to: str = Field(..., env="EMAIL_TO")
    discord_webhook: Optional[str] = Field(None, env="DISCORD_WEBHOOK")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 2.2 API Gateway

```python
# api/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
from redis import Redis
import json

app = FastAPI(title="Research Swarm API")
redis_client = Redis.from_url(settings.redis_url)

class IdeaSubmission(BaseModel):
    idea: str
    priority: str = "medium"
    context: Optional[str] = None
    constraints: Optional[dict] = None

class IdeaResponse(BaseModel):
    idea_id: str
    status: str
    estimated_completion: datetime
    tracking_url: str

@app.post("/api/v1/ideas", response_model=IdeaResponse)
async def submit_idea(
    submission: IdeaSubmission,
    background_tasks: BackgroundTasks
):
    # Generate unique ID
    idea_id = str(uuid.uuid4())
    
    # Create job payload
    job_data = {
        "idea_id": idea_id,
        "idea": submission.idea,
        "priority": submission.priority,
        "context": submission.context,
        "constraints": submission.constraints,
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "queued"
    }
    
    # Queue for processing
    redis_client.lpush("idea_queue", json.dumps(job_data))
    
    # Store metadata
    redis_client.hset(f"idea:{idea_id}", mapping=job_data)
    
    # Calculate estimated completion
    queue_length = redis_client.llen("idea_queue")
    estimated_minutes = queue_length * 30  # 30 min average per idea
    estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_minutes)
    
    return IdeaResponse(
        idea_id=idea_id,
        status="queued",
        estimated_completion=estimated_completion,
        tracking_url=f"https://localhost:8000/ideas/{idea_id}"
    )

@app.get("/api/v1/ideas/{idea_id}/status")
async def get_idea_status(idea_id: str):
    data = redis_client.hgetall(f"idea:{idea_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "idea_id": idea_id,
        "status": data.get(b"status", b"unknown").decode(),
        "current_phase": data.get(b"phase", b"").decode(),
        "progress_percentage": int(data.get(b"progress", 0)),
        "result_url": data.get(b"result_url", b"").decode() or None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2.3 LangGraph Orchestrator

```python
# orchestrator/workflow.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Literal
import asyncio
from agents.planner import PlannerAgent
from agents.researcher import ResearchSwarm
from agents.builder import BuilderAgent
from agents.tester import TesterAgent

class IdeaState(TypedDict):
    idea_id: str
    idea_text: str
    complexity: Literal["simple", "medium", "complex"]
    needs_research: bool
    research_results: Optional[List[dict]]
    implementation_plan: Optional[dict]
    code_artifacts: Optional[List[str]]
    test_results: Optional[dict]
    iteration_count: int
    final_output: Optional[dict]
    errors: List[str]

class ResearchWorkflow:
    def __init__(self):
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self):
        workflow = StateGraph(IdeaState)
        
        # Add nodes
        workflow.add_node("plan", self.plan_idea)
        workflow.add_node("research", self.research_idea)
        workflow.add_node("synthesize", self.synthesize_research)
        workflow.add_node("decompose", self.decompose_tasks)
        workflow.add_node("build", self.build_implementation)
        workflow.add_node("test", self.test_implementation)
        workflow.add_node("report", self.generate_report)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "plan",
            self.should_research,
            {
                True: "research",
                False: "decompose"
            }
        )
        
        workflow.add_edge("research", "synthesize")
        workflow.add_edge("synthesize", "decompose")
        
        workflow.add_conditional_edges(
            "decompose",
            self.is_feasible,
            {
                True: "build",
                False: "report"
            }
        )
        
        workflow.add_conditional_edges(
            "build",
            self.check_build_status,
            {
                "success": "test",
                "retry": "build",
                "fail": "report"
            }
        )
        
        workflow.add_edge("test", "report")
        workflow.add_edge("report", END)
        
        # Set entry point
        workflow.set_entry_point("plan")
        
        return workflow
    
    async def plan_idea(self, state: IdeaState) -> IdeaState:
        planner = PlannerAgent()
        result = await planner.analyze(state["idea_text"])
        
        state["complexity"] = result["complexity"]
        state["needs_research"] = result["needs_research"]
        state["implementation_plan"] = result["initial_plan"]
        
        return state
    
    async def research_idea(self, state: IdeaState) -> IdeaState:
        swarm = ResearchSwarm()
        research_results = await swarm.research(
            idea=state["idea_text"],
            areas=state["implementation_plan"].get("research_areas", [])
        )
        
        state["research_results"] = research_results
        return state
    
    async def synthesize_research(self, state: IdeaState) -> IdeaState:
        # Synthesize research findings
        synthesis = await self._synthesize_findings(state["research_results"])
        state["implementation_plan"]["synthesis"] = synthesis
        return state
    
    async def decompose_tasks(self, state: IdeaState) -> IdeaState:
        # Decompose into atomic tasks
        tasks = await self._decompose_plan(state["implementation_plan"])
        state["implementation_plan"]["tasks"] = tasks
        return state
    
    async def build_implementation(self, state: IdeaState) -> IdeaState:
        builder = BuilderAgent()
        
        state["iteration_count"] += 1
        
        result = await builder.build(
            plan=state["implementation_plan"],
            iteration=state["iteration_count"]
        )
        
        if result["status"] == "success":
            state["code_artifacts"] = result["artifacts"]
        else:
            state["errors"].append(result["error"])
        
        return state
    
    async def test_implementation(self, state: IdeaState) -> IdeaState:
        tester = TesterAgent()
        
        test_results = await tester.test(
            artifacts=state["code_artifacts"],
            requirements=state["implementation_plan"]["requirements"]
        )
        
        state["test_results"] = test_results
        return state
    
    async def generate_report(self, state: IdeaState) -> IdeaState:
        # Generate final report
        report = await self._create_report(state)
        state["final_output"] = report
        return state
    
    def should_research(self, state: IdeaState) -> bool:
        return state["needs_research"]
    
    def is_feasible(self, state: IdeaState) -> bool:
        return state["implementation_plan"].get("feasible", False)
    
    def check_build_status(self, state: IdeaState) -> str:
        if state["code_artifacts"]:
            return "success"
        elif state["iteration_count"] < settings.max_iterations:
            return "retry"
        else:
            return "fail"
    
    async def process_idea(self, idea_text: str, idea_id: str) -> dict:
        initial_state = {
            "idea_id": idea_id,
            "idea_text": idea_text,
            "complexity": "unknown",
            "needs_research": False,
            "research_results": None,
            "implementation_plan": None,
            "code_artifacts": None,
            "test_results": None,
            "iteration_count": 0,
            "final_output": None,
            "errors": []
        }
        
        final_state = await self.app.ainvoke(initial_state)
        return final_state["final_output"]
```

### 2.4 Agent Implementations

```python
# agents/planner.py
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

class PlannerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.1,
            model="gpt-4"
        )
        self.prompt = ChatPromptTemplate.from_template("""
        Analyze the following idea and create an initial plan.
        
        Idea: {idea}
        
        Provide a JSON response with:
        1. complexity: "simple", "medium", or "complex"
        2. needs_research: boolean
        3. research_areas: list of topics to research
        4. initial_plan: high-level implementation steps
        5. estimated_effort: in minutes
        6. feasibility_score: 0-1
        
        Be realistic about complexity and effort.
        """)
    
    async def analyze(self, idea: str) -> dict:
        chain = self.prompt | self.llm
        response = await chain.ainvoke({"idea": idea})
        
        # Parse JSON response
        result = json.loads(response.content)
        
        # Validate and set defaults
        result["complexity"] = result.get("complexity", "medium")
        result["needs_research"] = result.get("needs_research", True)
        
        return result
```

```python
# agents/researcher.py
import asyncio
from typing import List, Dict
from langchain.tools import Tool
from langchain.utilities import SerpAPIWrapper, ArxivAPIWrapper
from langchain.document_loaders import WebBaseLoader
import aiohttp

class ResearchAgent:
    def __init__(self, specialty: str):
        self.specialty = specialty
        self.tools = self._setup_tools()
    
    def _setup_tools(self):
        tools = []
        
        if self.specialty == "api":
            # API documentation search
            tools.append(
                Tool(
                    name="api_search",
                    func=self._search_apis,
                    description="Search for API documentation"
                )
            )
        elif self.specialty == "code":
            # Code example search
            tools.append(
                Tool(
                    name="code_search",
                    func=self._search_code,
                    description="Search for code examples"
                )
            )
        elif self.specialty == "papers":
            # Academic paper search
            arxiv = ArxivAPIWrapper()
            tools.append(
                Tool(
                    name="arxiv_search",
                    func=arxiv.run,
                    description="Search academic papers"
                )
            )
        
        return tools
    
    async def research(self, query: str) -> Dict:
        results = []
        for tool in self.tools:
            try:
                result = await asyncio.to_thread(tool.func, query)
                results.append({
                    "source": tool.name,
                    "content": result
                })
            except Exception as e:
                results.append({
                    "source": tool.name,
                    "error": str(e)
                })
        
        return {
            "agent": self.specialty,
            "query": query,
            "findings": results
        }

class ResearchSwarm:
    def __init__(self):
        self.agents = [
            ResearchAgent("api"),
            ResearchAgent("code"),
            ResearchAgent("papers"),
            ResearchAgent("tools")
        ]
    
    async def research(self, idea: str, areas: List[str]) -> List[Dict]:
        tasks = []
        for area in areas:
            for agent in self.agents:
                tasks.append(agent.research(f"{idea} {area}"))
        
        results = await asyncio.gather(*tasks)
        return results
```

```python
# agents/builder.py
import os
import subprocess
from typing import Dict, List
from pathlib import Path
import black
import autopep8

class BuilderAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.2, model="gpt-4")
        self.supported_languages = ["python", "javascript", "typescript", "swift"]
    
    async def build(self, plan: Dict, iteration: int) -> Dict:
        try:
            # Select optimal tool/framework
            tool = self._select_tool(plan)
            
            # Generate code following TDD
            code_files = await self._generate_code(plan, tool, iteration)
            
            # Format code
            formatted_files = self._format_code(code_files)
            
            # Basic validation
            if self._validate_code(formatted_files):
                return {
                    "status": "success",
                    "artifacts": formatted_files,
                    "tool": tool
                }
            else:
                return {
                    "status": "retry",
                    "error": "Code validation failed"
                }
        except Exception as e:
            return {
                "status": "fail" if iteration >= 10 else "retry",
                "error": str(e)
            }
    
    def _select_tool(self, plan: Dict) -> str:
        """Select easiest tool for the job"""
        requirements = plan.get("requirements", {})
        
        if requirements.get("type") == "web_app":
            return "streamlit"  # Easiest for quick prototypes
        elif requirements.get("type") == "api":
            return "fastapi"
        elif requirements.get("type") == "mobile":
            return "pwa"  # Progressive Web App
        elif requirements.get("type") == "extension":
            return "manifest_v3"
        else:
            return "python"  # Default
    
    async def _generate_code(self, plan: Dict, tool: str, iteration: int) -> List[Dict]:
        # First, generate test
        test_prompt = f"""
        Generate a test file for the following plan:
        {plan}
        
        Use {tool} and follow TDD principles.
        This is iteration {iteration}, so focus on core functionality.
        """
        
        test_code = await self.llm.ainvoke(test_prompt)
        
        # Then, generate implementation
        impl_prompt = f"""
        Generate implementation to pass this test:
        {test_code.content}
        
        Use {tool} and keep it simple.
        """
        
        impl_code = await self.llm.ainvoke(impl_prompt)
        
        return [
            {"name": "test_main.py", "content": test_code.content},
            {"name": "main.py", "content": impl_code.content}
        ]
    
    def _format_code(self, files: List[Dict]) -> List[Dict]:
        """Format code based on language"""
        formatted = []
        for file in files:
            content = file["content"]
            if file["name"].endswith(".py"):
                try:
                    content = black.format_str(content, mode=black.Mode())
                except:
                    content = autopep8.fix_code(content)
            
            formatted.append({
                "name": file["name"],
                "content": content
            })
        
        return formatted
    
    def _validate_code(self, files: List[Dict]) -> bool:
        """Basic syntax validation"""
        for file in files:
            if file["name"].endswith(".py"):
                try:
                    compile(file["content"], file["name"], "exec")
                except SyntaxError:
                    return False
        return True
```

```python
# agents/tester.py
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List
import pytest
import coverage

class TesterAgent:
    async def test(self, artifacts: List[Dict], requirements: Dict) -> Dict:
        # Create temp directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Write artifacts to temp directory
            for artifact in artifacts:
                file_path = tmppath / artifact["name"]
                file_path.write_text(artifact["content"])
            
            # Run tests based on file type
            test_results = await self._run_tests(tmppath)
            
            # Run coverage analysis
            coverage_results = await self._run_coverage(tmppath)
            
            # Run E2E tests if applicable
            e2e_results = await self._run_e2e_tests(tmppath, requirements)
            
            return {
                "unit_tests": test_results,
                "coverage": coverage_results,
                "e2e_tests": e2e_results,
                "passed": self._all_tests_passed(test_results, e2e_results)
            }
    
    async def _run_tests(self, path: Path) -> Dict:
        # Find test files
        test_files = list(path.glob("test_*.py"))
        
        if not test_files:
            return {"status": "no_tests", "passed": True}
        
        # Run pytest
        result = subprocess.run(
            ["pytest", "-v", "--tb=short", "--json-report"],
            cwd=path,
            capture_output=True,
            text=True
        )
        
        return {
            "status": "completed",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    
    async def _run_coverage(self, path: Path) -> Dict:
        cov = coverage.Coverage()
        cov.start()
        
        # Run code under coverage
        try:
            pytest.main([str(path)])
        except:
            pass
        
        cov.stop()
        cov.save()
        
        # Get coverage percentage
        total = cov.report()
        
        return {
            "percentage": total,
            "meets_threshold": total >= 70
        }
    
    async def _run_e2e_tests(self, path: Path, requirements: Dict) -> Dict:
        # Generate E2E test based on requirements
        e2e_test = self._generate_e2e_test(requirements)
        
        # Write E2E test
        e2e_path = path / "test_e2e.py"
        e2e_path.write_text(e2e_test)
        
        # Run E2E test
        result = subprocess.run(
            ["pytest", "test_e2e.py", "-v"],
            cwd=path,
            capture_output=True,
            text=True
        )
        
        return {
            "passed": result.returncode == 0,
            "output": result.stdout
        }
    
    def _generate_e2e_test(self, requirements: Dict) -> str:
        """Generate E2E test based on requirements"""
        return f"""
import pytest
from main import *

def test_end_to_end_workflow():
    # Test the complete workflow
    # Based on requirements: {requirements}
    
    # Setup
    # ... test setup code ...
    
    # Execute
    # ... test execution ...
    
    # Assert
    assert True  # Replace with actual assertions
"""
    
    def _all_tests_passed(self, unit_results: Dict, e2e_results: Dict) -> bool:
        return (
            unit_results.get("passed", False) and
            e2e_results.get("passed", False)
        )
```

---

## 3. Infrastructure Configuration

### 3.1 Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: research_swarm
      POSTGRES_USER: swarm
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://swarm:${DB_PASSWORD}@postgres:5432/research_swarm
    depends_on:
      - redis
      - postgres
    volumes:
      - ./outputs:/app/outputs

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://swarm:${DB_PASSWORD}@postgres:5432/research_swarm
    depends_on:
      - redis
      - postgres
    volumes:
      - ./outputs:/app/outputs
      - /var/run/docker.sock:/var/run/docker.sock  # For spawning pods

volumes:
  redis_data:
  postgres_data:
```

### 3.2 Kubernetes Configuration

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-swarm-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: research-swarm-api
  template:
    metadata:
      labels:
        app: research-swarm-api
    spec:
      containers:
      - name: api
        image: research-swarm:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        volumeMounts:
        - name: outputs
          mountPath: /app/outputs
      volumes:
      - name: outputs
        persistentVolumeClaim:
          claimName: research-outputs-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: research-swarm-api-service
spec:
  selector:
    app: research-swarm-api
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: batch/v1
kind: Job
metadata:
  name: research-job-template
spec:
  template:
    spec:
      containers:
      - name: research-worker
        image: research-swarm-worker:latest
        env:
        - name: IDEA_ID
          value: "PLACEHOLDER"
        - name: PHASE
          value: "PLACEHOLDER"
      restartPolicy: OnFailure
  backoffLimit: 3
```

### 3.3 Pod Templates

```yaml
# k8s/pod-templates/planner-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: planner-pod-template
spec:
  containers:
  - name: planner
    image: python:3.11-slim
    command: ["python", "/app/planner.py"]
    resources:
      requests:
        memory: "512Mi"
        cpu: "500m"
      limits:
        memory: "1Gi"
        cpu: "1000m"
    env:
    - name: OPENAI_API_KEY
      valueFrom:
        secretKeyRef:
          name: api-keys
          key: openai
    volumeMounts:
    - name: workspace
      mountPath: /workspace
  volumes:
  - name: workspace
    emptyDir: {}
  restartPolicy: Never
  activeDeadlineSeconds: 300  # 5 minute timeout
```

---

## 4. iOS Shortcut Configuration

### 4.1 Shortcut Definition

```json
{
  "name": "Research This",
  "description": "Send idea to research swarm",
  "actions": [
    {
      "type": "text_input",
      "prompt": "What's your idea?",
      "variable": "idea_text"
    },
    {
      "type": "get_network",
      "network_type": "tailscale"
    },
    {
      "type": "http_request",
      "method": "POST",
      "url": "https://100.x.x.x:8000/api/v1/ideas",
      "headers": {
        "Content-Type": "application/json",
        "X-Device-ID": "{device_id}"
      },
      "body": {
        "idea": "{idea_text}",
        "priority": "medium"
      },
      "variable": "response"
    },
    {
      "type": "parse_json",
      "json": "{response}",
      "keys": ["idea_id", "tracking_url"],
      "variable": "result"
    },
    {
      "type": "notification",
      "title": "Idea Submitted",
      "body": "ID: {result.idea_id}",
      "url": "{result.tracking_url}"
    }
  ],
  "triggers": [
    {
      "type": "back_tap",
      "taps": 2
    },
    {
      "type": "widget"
    },
    {
      "type": "siri",
      "phrase": "research idea"
    }
  ]
}
```

### 4.2 Tailscale Setup

```bash
# Install Tailscale on server
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up --authkey=$TAILSCALE_AUTH_KEY

# Get Tailscale IP
tailscale ip -4

# Configure ACLs in Tailscale admin panel
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:mobile"],
      "dst": ["tag:server:8000"]
    }
  ],
  "tagOwners": {
    "tag:mobile": ["user@example.com"],
    "tag:server": ["user@example.com"]
  }
}
```

---

## 5. Output Repository Management

### 5.1 Git Repository Handler

```python
# utils/repository.py
import git
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List

class RepositoryManager:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(self.repo_path)
    
    def create_idea_folder(self, idea_id: str, idea_text: str) -> Path:
        # Create folder with timestamp and sanitized name
        timestamp = datetime.now().strftime("%Y-%m-%d")
        safe_name = self._sanitize_name(idea_text[:50])
        folder_name = f"{timestamp}-{safe_name}"
        
        idea_path = self.repo_path / "ideas" / folder_name
        idea_path.mkdir(parents=True, exist_ok=True)
        
        # Create metadata file
        metadata = {
            "idea_id": idea_id,
            "idea_text": idea_text,
            "created_at": datetime.now().isoformat(),
            "status": "processing"
        }
        
        (idea_path / "metadata.json").write_text(
            json.dumps(metadata, indent=2)
        )
        
        # Create subdirectories
        for subdir in ["research", "plan", "implementation", "results"]:
            (idea_path / subdir).mkdir(exist_ok=True)
        
        # Initial commit
        self.repo.index.add([str(idea_path)])
        self.repo.index.commit(f"Initialize idea: {safe_name}")
        
        return idea_path
    
    def save_research(self, idea_path: Path, research: Dict):
        research_path = idea_path / "research"
        
        # Save main research document
        readme = self._generate_research_readme(research)
        (research_path / "README.md").write_text(readme)
        
        # Save feasibility analysis
        feasibility = self._analyze_feasibility(research)
        (research_path / "feasibility.md").write_text(feasibility)
        
        # Save references
        refs = self._extract_references(research)
        (research_path / "references.md").write_text(refs)
        
        # Commit
        self.repo.index.add([str(research_path)])
        self.repo.index.commit(f"Add research for {idea_path.name}")
    
    def save_implementation(self, idea_path: Path, artifacts: List[Dict]):
        impl_path = idea_path / "implementation"
        
        for artifact in artifacts:
            file_path = impl_path / artifact["name"]
            file_path.write_text(artifact["content"])
        
        # Create README
        readme = self._generate_impl_readme(artifacts)
        (impl_path / "README.md").write_text(readme)
        
        # Commit
        self.repo.index.add([str(impl_path)])
        self.repo.index.commit(f"Add implementation for {idea_path.name}")
    
    def save_test_results(self, idea_path: Path, test_results: Dict):
        results_path = idea_path / "results"
        
        # Save test report
        report = self._generate_test_report(test_results)
        (results_path / "test-report.md").write_text(report)
        
        # Save coverage if available
        if "coverage" in test_results:
            (results_path / "coverage.json").write_text(
                json.dumps(test_results["coverage"], indent=2)
            )
        
        # Commit
        self.repo.index.add([str(results_path)])
        self.repo.index.commit(f"Add test results for {idea_path.name}")
    
    def finalize_idea(self, idea_path: Path, summary: Dict):
        # Update metadata
        metadata_path = idea_path / "metadata.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["status"] = "completed"
        metadata["completed_at"] = datetime.now().isoformat()
        metadata["summary"] = summary
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        # Create final summary
        summary_text = self._generate_summary(summary)
        (idea_path / "SUMMARY.md").write_text(summary_text)
        
        # Final commit
        self.repo.index.add([str(idea_path)])
        self.repo.index.commit(f"Complete processing for {idea_path.name}")
        
        # Push to remote if configured
        if self.repo.remotes:
            self.repo.remotes.origin.push()
    
    def _sanitize_name(self, text: str) -> str:
        # Remove special characters and spaces
        import re
        safe = re.sub(r'[^\w\s-]', '', text.lower())
        safe = re.sub(r'[-\s]+', '-', safe)
        return safe[:50]
    
    def _generate_research_readme(self, research: Dict) -> str:
        return f"""# Research Summary

## Overview
{research.get('overview', 'No overview available')}

## Key Findings
{self._format_findings(research.get('findings', []))}

## Technical Analysis
{research.get('technical_analysis', 'No analysis available')}

## Recommendations
{research.get('recommendations', 'No recommendations')}

## Next Steps
{research.get('next_steps', 'No next steps defined')}
"""
    
    def _generate_test_report(self, test_results: Dict) -> str:
        return f"""# Test Report

## Summary
- **Unit Tests**: {test_results['unit_tests']['passed']}
- **Coverage**: {test_results['coverage']['percentage']}%
- **E2E Tests**: {test_results['e2e_tests']['passed']}

## Details
{json.dumps(test_results, indent=2)}
"""
```

---

## 6. Monitoring & Observability

### 6.1 Logging Configuration

```python
# utils/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime

def setup_logging(app_name: str = "research-swarm"):
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    
    # JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(f"/logs/{app_name}.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()
```

### 6.2 Metrics Collection

```python
# utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Define metrics
ideas_processed = Counter('ideas_processed_total', 'Total ideas processed')
ideas_failed = Counter('ideas_failed_total', 'Total ideas failed')
processing_time = Histogram('processing_time_seconds', 'Time to process idea')
queue_depth = Gauge('queue_depth', 'Current queue depth')
active_pods = Gauge('active_pods', 'Number of active pods')

class MetricsCollector:
    @staticmethod
    def record_idea_processed(success: bool, duration: float):
        if success:
            ideas_processed.inc()
        else:
            ideas_failed.inc()
        processing_time.observe(duration)
    
    @staticmethod
    def update_queue_depth(depth: int):
        queue_depth.set(depth)
    
    @staticmethod
    def update_active_pods(count: int):
        active_pods.set(count)

# Start Prometheus metrics server
start_http_server(9090)
```

---

## 7. Deployment Instructions

### 7.1 Local Development

```bash
# 1. Clone repository
git clone <your-repo-url>
cd research-swarm

# 2. Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-...
SERPAPI_API_KEY=...
TAILSCALE_AUTH_KEY=tskey-...
DB_PASSWORD=secure_password
EMAIL_FROM=you@example.com
EMAIL_TO=you@example.com
REPO_PATH=/home/user/research-output
EOF

# 3. Start services
docker-compose up -d

# 4. Initialize database
python scripts/init_db.py

# 5. Start worker
python orchestrator/worker.py

# 6. Test API
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Test idea for processing"}'
```

### 7.2 Production Deployment

```bash
# 1. Build Docker images
docker build -t research-swarm-api:latest -f Dockerfile.api .
docker build -t research-swarm-worker:latest -f Dockerfile.worker .

# 2. Push to registry
docker tag research-swarm-api:latest your-registry/research-swarm-api:latest
docker push your-registry/research-swarm-api:latest

# 3. Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 4. Configure Tailscale
kubectl apply -f k8s/tailscale-sidecar.yaml

# 5. Monitor deployment
kubectl get pods -n research-swarm
kubectl logs -f deployment/research-swarm-api -n research-swarm
```

---

## 8. Testing Guide

### 8.1 Unit Tests

```python
# tests/test_planner.py
import pytest
from agents.planner import PlannerAgent

@pytest.mark.asyncio
async def test_planner_simple_idea():
    planner = PlannerAgent()
    result = await planner.analyze("Create a hello world app")
    
    assert result["complexity"] == "simple"
    assert not result["needs_research"]
    assert result["feasibility_score"] > 0.8
```

### 8.2 Integration Tests

```python
# tests/test_workflow.py
import pytest
from orchestrator.workflow import ResearchWorkflow

@pytest.mark.asyncio
async def test_complete_workflow():
    workflow = ResearchWorkflow()
    
    result = await workflow.process_idea(
        idea_text="Build a weather notification app",
        idea_id="test-001"
    )
    
    assert result is not None
    assert "implementation" in result
    assert "test_results" in result
```

### 8.3 E2E Tests

```bash
# tests/e2e_test.sh
#!/bin/bash

# Submit idea
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a TODO app with React"}')

# Extract idea ID
IDEA_ID=$(echo $RESPONSE | jq -r '.idea_id')

# Wait for processing
sleep 60

# Check status
STATUS=$(curl -s http://localhost:8000/api/v1/ideas/$IDEA_ID/status | jq -r '.status')

# Verify completion
if [ "$STATUS" = "completed" ]; then
  echo "E2E Test Passed"
  exit 0
else
  echo "E2E Test Failed: Status is $STATUS"
  exit 1
fi
```

---

## Troubleshooting Guide

### Common Issues and Solutions

1. **Redis Connection Failed**
   - Check Redis is running: `docker ps | grep redis`
   - Verify connection string in .env

2. **API Key Errors**
   - Ensure all API keys are set in .env
   - Check rate limits on external APIs

3. **Pod Timeout**
   - Increase timeout values in settings
   - Check resource limits in K8s

4. **Git Push Failed**
   - Verify Git credentials
   - Check repository permissions

---

This implementation guide provides the complete technical foundation for building your Research Automation Swarm system. Follow the sections in order for a smooth implementation process.