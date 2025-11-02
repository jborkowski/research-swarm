import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch, MagicMock
from orchestrator.workflow import ResearchWorkflow
from config.settings import settings


class TestIntegrationWorkflow:
    """Integration tests for the complete research workflow"""

    @pytest.fixture
    def temp_repo_path(self):
        """Create a temporary directory for repository operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_settings(self, temp_repo_path):
        """Mock settings for testing"""
        with patch.object(settings, 'repository_path', temp_repo_path), \
             patch.object(settings, 'max_iterations', 2), \
             patch.object(settings, 'openai_api_key', 'test-key'), \
             patch.object(settings, 'serpapi_api_key', 'test-serpapi-key'), \
             patch.object(settings, 'redis_url', 'redis://localhost:6379'):

            # Initialize git repo in temp directory
            os.system(f"cd {temp_repo_path} && git init")
            yield settings

    @pytest.mark.asyncio
    async def test_full_workflow_simple_idea(self, mock_settings):
        """Test complete workflow with a simple idea that doesn't need research"""
        workflow = ResearchWorkflow()

        # Mock the planner to return a simple idea
        with patch('agents.planner.PlannerAgent.analyze') as mock_planner:
            mock_planner.return_value = {
                "complexity": "simple",
                "needs_research": False,
                "initial_plan": {
                    "description": "Simple print function",
                    "requirements": {"output": "Hello World"}
                }
            }

            # Mock builder to return success
            with patch('agents.builder.BuilderAgent.build') as mock_builder:
                mock_builder.return_value = {
                    "status": "success",
                    "artifacts": [{"file": "hello.py", "content": "print('Hello World')"}]
                }

                # Mock tester to return success
                with patch('agents.tester.TesterAgent.test') as mock_tester:
                    mock_tester.return_value = {
                        "passed": True,
                        "coverage": 100.0,
                        "results": []
                    }

                    result = await workflow.process_idea(
                        "Create a hello world program",
                        "test-idea-001"
                    )

                    assert result["status"] == "completed"
                    assert result["idea_id"] == "test-idea-001"
                    assert result["test_results"]["passed"] is True
                    assert len(result["implementation"]) > 0
                    assert "print('Hello World')" in result["implementation"][0]["content"]

    @pytest.mark.asyncio
    async def test_workflow_with_research(self, mock_settings):
        """Test workflow that includes research phase"""
        workflow = ResearchWorkflow()

        # Mock ResearchAgent to avoid API key issues
        with patch('agents.researcher.ResearchAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.research.return_value = {
                "agent": "api",
                "query": "Build a weather API client REST APIs",
                "findings": [
                    {"source": "api_search", "content": "REST API available for weather data"}
                ]
            }
            mock_agent_class.return_value = mock_agent

            # Mock planner - needs research
            with patch('agents.planner.PlannerAgent.analyze') as mock_planner:
                mock_planner.return_value = {
                    "complexity": "complex",
                    "needs_research": True,
                    "initial_plan": {
                        "description": "Complex API integration",
                        "research_areas": ["REST APIs", "authentication"]
                    }
                }

                # Mock research swarm
                with patch('agents.researcher.ResearchSwarm.research') as mock_research:
                    mock_research.return_value = [
                        {
                            "agent": "api",
                            "findings": [
                                {"content": "REST API available for weather data", "confidence": 0.9}
                            ]
                        },
                        {
                            "agent": "code",
                            "findings": [
                                {"content": "Python requests library for API calls", "confidence": 0.8}
                            ]
                        },
                        {
                            "agent": "tools",
                            "findings": [
                                {"content": "OpenWeatherMap API tool available", "confidence": 0.7}
                            ]
                        }
                    ]

                    # Mock builder
                    with patch('agents.builder.BuilderAgent.build') as mock_builder:
                        mock_builder.return_value = {
                            "status": "success",
                            "artifacts": [{"file": "weather_api.py", "content": "# Weather API code"}]
                        }

                        # Mock tester
                        with patch('agents.tester.TesterAgent.test') as mock_tester:
                            mock_tester.return_value = {
                                "passed": True,
                                "coverage": 85.0,
                                "results": []
                            }

                            result = await workflow.process_idea(
                                "Build a weather API client",
                                "test-idea-002"
                            )

                            assert result["status"] == "completed"
                            assert result["research_results"] is not None
                            assert len(result["research_results"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_build_failure_retry(self, mock_settings):
        """Test workflow that retries on build failure"""
        workflow = ResearchWorkflow()

        # Mock planner
        with patch('agents.planner.PlannerAgent.analyze') as mock_planner:
            mock_planner.return_value = {
                "complexity": "medium",
                "needs_research": False,
                "initial_plan": {"description": "Test implementation"}
            }

            # Mock builder - fail first, succeed second
            with patch('agents.builder.BuilderAgent.build') as mock_builder:
                mock_builder.side_effect = [
                    {"status": "error", "error": "Syntax error"},
                    {"status": "success", "artifacts": [{"file": "test.py", "content": "print('fixed')"}]}
                ]

                # Mock tester
                with patch('agents.tester.TesterAgent.test') as mock_tester:
                    mock_tester.return_value = {
                        "passed": True,
                        "coverage": 90.0,
                        "results": []
                    }

                    result = await workflow.process_idea(
                        "Fix syntax errors",
                        "test-idea-003"
                    )

                    assert result["status"] == "completed"
                    assert result["iterations_used"] == 2  # Should have retried
                    assert mock_builder.call_count == 2

    @pytest.mark.asyncio
    async def test_workflow_max_iterations_exceeded(self, mock_settings):
        """Test workflow that fails after max iterations"""
        workflow = ResearchWorkflow()

        # Mock planner
        with patch('agents.planner.PlannerAgent.analyze') as mock_planner:
            mock_planner.return_value = {
                "complexity": "complex",
                "needs_research": False,
                "initial_plan": {"description": "Impossible task"}
            }

            # Mock builder - always fail
            with patch('agents.builder.BuilderAgent.build') as mock_builder:
                mock_builder.return_value = {
                    "status": "error",
                    "error": "Persistent failure"
                }

                result = await workflow.process_idea(
                    "Impossible implementation",
                    "test-idea-004"
                )

                assert result["status"] == "failed"
                assert result["iterations_used"] == 2  # max_iterations
                assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_infeasible_after_research(self, mock_settings):
        """Test workflow that determines idea is infeasible after research"""
        workflow = ResearchWorkflow()

        # Mock ResearchAgent to avoid API key issues
        with patch('agents.researcher.ResearchAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.research.return_value = {
                "agent": "papers",
                "query": "Build quantum computer quantum computing",
                "findings": [
                    {"source": "arxiv_search", "content": "Quantum computing requires millions in funding"}
                ]
            }
            mock_agent_class.return_value = mock_agent

            # Mock planner - needs research
            with patch('agents.planner.PlannerAgent.analyze') as mock_planner:
                mock_planner.return_value = {
                    "complexity": "complex",
                    "needs_research": True,
                    "initial_plan": {
                        "description": "Quantum computer at home",
                        "research_areas": ["quantum computing"]
                    }
                }

                # Mock research - no feasible results
                with patch('agents.researcher.ResearchSwarm.research') as mock_research:
                    mock_research.return_value = [
                        {
                            "agent": "papers",
                            "findings": [
                                {"content": "Quantum computing requires millions in funding", "confidence": 0.1}
                            ]
                        }
                    ]

                    result = await workflow.process_idea(
                        "Build quantum computer",
                        "test-idea-005"
                    )

                    assert result["status"] == "failed"
                    assert "infeasible" in result["summary"].lower() or "not feasible" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, mock_settings):
        """Test workflow error handling and notifications"""
        workflow = ResearchWorkflow()

        # Mock planner to raise exception
        with patch('agents.planner.PlannerAgent.analyze') as mock_planner:
            mock_planner.side_effect = Exception("Planner service unavailable")

            result = await workflow.process_idea(
                "Test error handling",
                "test-idea-006"
            )

            assert result["status"] == "error"
            assert "Planner service unavailable" in result["errors"][0]
            assert len(result["errors"]) > 0