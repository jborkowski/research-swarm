import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from agents.researcher import ResearchAgent, ResearchSwarm


@pytest.mark.asyncio
async def test_research_agent_api_specialty():
    """Test ResearchAgent with API specialty"""
    agent = ResearchAgent("api")
    assert agent.specialty == "api"
    assert len(agent.tools) > 0


@pytest.mark.asyncio
async def test_research_agent_code_specialty():
    """Test ResearchAgent with code specialty"""
    agent = ResearchAgent("code")
    assert agent.specialty == "code"
    assert len(agent.tools) > 0


@pytest.mark.asyncio
async def test_research_agent_papers_specialty():
    """Test ResearchAgent with papers specialty"""
    agent = ResearchAgent("papers")
    assert agent.specialty == "papers"
    assert len(agent.tools) > 0


@pytest.mark.asyncio
async def test_research_agent_tools_specialty():
    """Test ResearchAgent with tools specialty"""
    agent = ResearchAgent("tools")
    assert agent.specialty == "tools"
    assert len(agent.tools) > 0


@pytest.mark.asyncio
async def test_research_agent_research_success():
    """Test ResearchAgent research method with successful tool execution"""
    with patch('agents.researcher.SerpAPIWrapper') as mock_serp_wrapper:
        mock_tool_instance = MagicMock()
        mock_tool_instance.run.return_value = "Test result"
        mock_serp_wrapper.return_value = mock_tool_instance
        
        agent = ResearchAgent("api")  # This will use SerpAPIWrapper
        result = await agent.research("test query")
        
        assert result["agent"] == "api"
        assert result["query"] == "test query"
        assert len(result["findings"]) > 0


@pytest.mark.asyncio
async def test_research_agent_research_with_error():
    """Test ResearchAgent research method when tool execution fails"""
    with patch('agents.researcher.SerpAPIWrapper') as mock_serp_wrapper:
        mock_tool_instance = MagicMock()
        mock_tool_instance.run.side_effect = Exception("API Error")
        mock_serp_wrapper.return_value = mock_tool_instance
        
        agent = ResearchAgent("api")
        result = await agent.research("test query")
        
        assert result["agent"] == "api"
        assert result["query"] == "test query"
        assert len(result["findings"]) > 0
        assert result["findings"][0]["error"] == "API Error"


@pytest.mark.asyncio
async def test_research_swarm_creation():
    """Test ResearchSwarm creation and agent initialization"""
    swarm = ResearchSwarm()
    assert len(swarm.agents) == 4
    assert swarm.agents[0].specialty == "api"
    assert swarm.agents[1].specialty == "code"
    assert swarm.agents[2].specialty == "papers"
    assert swarm.agents[3].specialty == "tools"


@pytest.mark.asyncio
async def test_research_swarm_research():
    """Test ResearchSwarm research method"""
    with patch('agents.researcher.SerpAPIWrapper') as mock_serp_wrapper, \
         patch('agents.researcher.ArxivAPIWrapper') as mock_arxiv_wrapper:
        
        # Mock the tools
        mock_serp_instance = MagicMock()
        mock_serp_instance.run.return_value = "Test API result"
        mock_serp_wrapper.return_value = mock_serp_instance
        
        mock_arxiv_instance = MagicMock()
        mock_arxiv_instance.run.return_value = "Test paper result" 
        mock_arxiv_wrapper.return_value = mock_arxiv_instance
        
        swarm = ResearchSwarm()
        results = await swarm.research("test idea", ["area1"])
        
        # Should have 4 results (one from each agent type for each area)
        assert len(results) == 4


def test_research_agent_setup_tools_api():
    """Test _setup_tools method for API specialty"""
    agent = ResearchAgent("api")
    assert len(agent.tools) > 0
    assert agent.tools[0].name == "api_search"


def test_research_agent_setup_tools_code():
    """Test _setup_tools method for code specialty"""
    agent = ResearchAgent("code")
    assert len(agent.tools) > 0
    assert agent.tools[0].name == "code_search"


def test_research_agent_setup_tools_papers():
    """Test _setup_tools method for papers specialty"""
    agent = ResearchAgent("papers")
    assert len(agent.tools) > 0
    assert agent.tools[0].name == "arxiv_search"


def test_research_agent_setup_tools_tools():
    """Test _setup_tools method for tools specialty"""
    agent = ResearchAgent("tools")
    assert len(agent.tools) > 0
    assert agent.tools[0].name == "tool_search"