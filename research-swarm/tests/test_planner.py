import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.planner import PlannerAgent


@pytest.mark.asyncio
async def test_planner_analyze_success():
    """Test planner analyze method with successful response"""
    with patch('agents.planner.ChatOpenAI') as mock_llm_class, \
         patch('agents.planner.ChatPromptTemplate') as mock_prompt_class:
        
        # Mock the LLM and prompt
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = '{"complexity": "simple", "needs_research": false, "research_areas": [], "initial_plan": {"steps": ["Implement basic functionality"]}, "estimated_effort": 60, "feasibility_score": 0.8}'
        mock_llm.ainvoke.return_value = mock_response
        
        mock_llm_class.return_value = mock_llm
        
        mock_prompt = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_template.return_value = mock_prompt
        
        planner = PlannerAgent()
        result = await planner.analyze("Create a hello world app")
        
        assert result["complexity"] in ["simple", "medium", "complex"]
        assert isinstance(result["needs_research"], bool)
        assert "initial_plan" in result


@pytest.mark.asyncio
async def test_planner_analyze_json_parse_error():
    """Test planner analyze method when JSON parsing fails"""
    with patch('agents.planner.ChatOpenAI') as mock_llm_class, \
         patch('agents.planner.ChatPromptTemplate') as mock_prompt_class:
        
        # Mock the LLM to return invalid JSON
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = 'invalid json response'
        mock_llm.ainvoke.return_value = mock_response
        
        mock_llm_class.return_value = mock_llm
        
        mock_prompt = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_response
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_template.return_value = mock_prompt
        
        planner = PlannerAgent()
        result = await planner.analyze("Create a hello world app")
        
        # Should have fallback values when JSON parsing fails
        assert result["complexity"] in ["simple", "medium", "complex"]
        assert isinstance(result["needs_research"], bool)
        assert "initial_plan" in result


@pytest.mark.asyncio
async def test_planner_analyze_exception():
    """Test planner analyze method when exception occurs"""
    with patch('agents.planner.ChatOpenAI') as mock_llm_class, \
         patch('agents.planner.ChatPromptTemplate') as mock_prompt_class:
        
        # Mock the LLM to raise an exception
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM Error")
        
        mock_llm_class.return_value = mock_llm
        
        mock_prompt = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = Exception("LLM Error")
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_template.return_value = mock_prompt
        
        planner = PlannerAgent()
        
        # Should handle exceptions gracefully
        with pytest.raises(Exception):
            await planner.analyze("Create a hello world app")


def test_planner_creation():
    """Test that planner agent can be created without error"""
    planner = PlannerAgent()
    assert planner is not None
    assert hasattr(planner, 'analyze')