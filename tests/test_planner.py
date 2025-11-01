import pytest
from agents.planner import PlannerAgent


@pytest.mark.asyncio
async def test_planner_simple_idea():
    """Test planner with a simple idea."""
    planner = PlannerAgent()

    result = await planner.analyze("Create a hello world Python script")

    assert result is not None
    assert "complexity" in result
    assert "needs_research" in result
    assert "feasible" in result
    assert result["complexity"] in ["simple", "medium", "complex"]


@pytest.mark.asyncio
async def test_planner_complex_idea():
    """Test planner with a complex idea."""
    planner = PlannerAgent()

    result = await planner.analyze(
        "Build a real-time collaborative document editing platform "
        "with WebRTC, operational transforms, and offline sync"
    )

    assert result is not None
    assert result["complexity"] in ["medium", "complex"]
    assert isinstance(result["needs_research"], bool)


@pytest.mark.asyncio
async def test_planner_with_context():
    """Test planner with additional context."""
    planner = PlannerAgent()

    result = await planner.analyze(
        "Create a TODO app",
        context="Should use React for frontend and FastAPI for backend"
    )

    assert result is not None
    assert "initial_plan" in result
    assert "requirements" in result["initial_plan"]
