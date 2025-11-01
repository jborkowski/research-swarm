import pytest
import asyncio
from agents.planner import PlannerAgent
from agents.researcher import ResearchSwarm
from agents.builder import BuilderAgent
from agents.tester import TesterAgent

@pytest.mark.asyncio
async def test_planner_agent():
    """Test the planner agent"""
    planner = PlannerAgent()
    result = await planner.analyze("Create a simple web app")
    
    assert result["complexity"] in ["simple", "medium", "complex"]
    assert "needs_research" in result
    assert "research_areas" in result
    assert "initial_plan" in result

@pytest.mark.asyncio
async def test_research_swarm():
    """Test the research swarm"""
    swarm = ResearchSwarm()
    results = await swarm.research("web app", ["api", "implementation"])
    
    assert isinstance(results, list)
    assert len(results) > 0
    for result in results:
        assert "agent" in result
        assert "query" in result
        assert "findings" in result

@pytest.mark.asyncio
async def test_builder_agent():
    """Test the builder agent"""
    builder = BuilderAgent()
    
    plan = {
        "idea_text": "Create a simple web app",
        "requirements": {"type": "web_app"}
    }
    
    result = await builder.build(plan, 1)
    
    assert result["status"] == "success"
    assert "artifacts" in result
    assert len(result["artifacts"]) > 0

@pytest.mark.asyncio
async def test_tester_agent():
    """Test the tester agent"""
    tester = TesterAgent()
    
    artifacts = [
        {"name": "main.py", "content": "print('hello')"},
        {"name": "test_main.py", "content": "import unittest\n\nclass TestMain(unittest.TestCase):\n    def test_example(self):\n        self.assertTrue(True)"}
    ]
    
    results = await tester.test(artifacts)
    
    assert "unit_tests" in results
    assert "coverage" in results
    assert "e2e_tests" in results

def test_imports():
    """Test that all modules can be imported"""
    from orchestrator.workflow import ResearchWorkflow
    from utils.repository import RepositoryManager
    
    # These should not raise ImportError
    assert ResearchWorkflow is not None
    assert RepositoryManager is not None