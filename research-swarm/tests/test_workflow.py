import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from orchestrator.workflow import ResearchWorkflow, IdeaState


@pytest.mark.asyncio
async def test_workflow_creation():
    """Test that workflow can be created and initialized"""
    with patch('orchestrator.workflow.StateGraph') as mock_graph:
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_app = MagicMock()
        mock_graph_instance.compile.return_value = mock_app
        
        workflow = ResearchWorkflow()
        
        assert workflow is not None
        assert workflow.workflow is not None
        assert workflow.app is not None


@pytest.mark.asyncio
async def test_plan_idea():
    """Test the plan_idea method"""
    with patch('orchestrator.workflow.StateGraph') as mock_graph, \
         patch('orchestrator.workflow.PlannerAgent') as mock_planner_class:
        
        # Setup mocks
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        mock_app = MagicMock()
        mock_graph_instance.compile.return_value = mock_app
        
        mock_planner = AsyncMock()
        mock_planner.analyze.return_value = {
            "complexity": "simple",
            "needs_research": False,
            "initial_plan": {"test": "plan"}
        }
        mock_planner_class.return_value = mock_planner
        
        workflow = ResearchWorkflow()
        initial_state = {
            "idea_id": "test-123",
            "idea_text": "test idea",
            "complexity": "unknown",
            "needs_research": False,
            "implementation_plan": None,
            "research_results": None,
            "code_artifacts": None,
            "test_results": None,
            "iteration_count": 0,
            "final_output": None,
            "errors": []
        }
        
        result = await workflow.plan_idea(initial_state)
        
        assert result["complexity"] == "simple"
        assert result["needs_research"] == False
        assert result["implementation_plan"] == {"test": "plan"}


@pytest.mark.asyncio
async def test_should_research():
    """Test the should_research method"""
    workflow = ResearchWorkflow()
    
    state_with_research = {"needs_research": True}
    state_without_research = {"needs_research": False}
    
    assert workflow.should_research(state_with_research) == True
    assert workflow.should_research(state_without_research) == False


@pytest.mark.asyncio
async def test_is_feasible():
    """Test the is_feasible method"""
    workflow = ResearchWorkflow()
    
    feasible_state = {"implementation_plan": {"feasible": True}}
    not_feasible_state = {"implementation_plan": {"feasible": False}}
    missing_plan_state = {"implementation_plan": {}}
    
    assert workflow.is_feasible(feasible_state) == True
    assert workflow.is_feasible(not_feasible_state) == False
    assert workflow.is_feasible(missing_plan_state) == False  # Should default to False


@pytest.mark.asyncio
async def test_check_build_status():
    """Test the check_build_status method"""
    from config.settings import settings
    workflow = ResearchWorkflow()
    
    # Test success case
    success_state = {"code_artifacts": ["file1.py"], "iteration_count": 1}
    assert workflow.check_build_status(success_state) == "success"
    
    # Test retry case
    retry_state = {"code_artifacts": None, "iteration_count": 5}
    assert workflow.check_build_status(retry_state) == "retry"
    
    # Test fail case (max iterations reached)
    fail_state = {"code_artifacts": None, "iteration_count": settings.max_iterations}
    assert workflow.check_build_status(fail_state) == "fail"


@pytest.mark.asyncio
async def test_process_idea():
    """Test the full process_idea method"""
    with patch('orchestrator.workflow.StateGraph') as mock_graph, \
         patch('orchestrator.workflow.PlannerAgent') as mock_planner_class, \
         patch('orchestrator.workflow.ResearchSwarm') as mock_swarm_class, \
         patch('orchestrator.workflow.BuilderAgent') as mock_builder_class, \
         patch('orchestrator.workflow.TesterAgent') as mock_tester_class:
        
        # Setup mocks
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        
        # Create a mock compiled app that returns a fixed result when invoked
        mock_app = AsyncMock()
        mock_app.ainvoke.return_value = {
            "final_output": {
                "idea_id": "test-123",
                "summary": "Test completed"
            }
        }
        mock_graph_instance.compile.return_value = mock_app
        
        # Mock agents
        mock_planner = AsyncMock()
        mock_planner.analyze.return_value = {
            "complexity": "simple", 
            "needs_research": False,
            "initial_plan": {"test": "plan"}
        }
        mock_planner_class.return_value = mock_planner
        
        mock_swarm = AsyncMock()
        mock_swarm.research.return_value = [{"test": "research"}]
        mock_swarm_class.return_value = mock_swarm
        
        mock_builder = AsyncMock()
        mock_builder.build.return_value = {"status": "success", "artifacts": []}
        mock_builder_class.return_value = mock_builder
        
        mock_tester = AsyncMock()
        mock_tester.test.return_value = {"passed": True}
        mock_tester_class.return_value = mock_tester
        
        workflow = ResearchWorkflow()
        
        result = await workflow.process_idea("test idea", "test-123")
        
        assert result is not None
        assert "summary" in result