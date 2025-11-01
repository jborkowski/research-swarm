import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.builder import BuilderAgent


@pytest.mark.asyncio
async def test_builder_build_success():
    """Test builder build method with successful code generation"""
    with patch('agents.builder.ChatOpenAI') as mock_llm_class, \
         patch('agents.builder.ChatPromptTemplate') as mock_prompt_class:
        
        # Mock the LLM
        mock_llm = AsyncMock()
        mock_test_response = MagicMock()
        mock_test_response.content = "def test_function():\n    assert True\n"
        mock_impl_response = MagicMock()
        mock_impl_response.content = "def function():\n    return True\n"
        
        # Mock the prompt chain to return different responses for test vs impl prompts
        call_count = 0
        def mock_ainvoke_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call for test generation
                return mock_test_response
            else:  # Second call for implementation generation
                return mock_impl_response
        
        mock_llm.ainvoke.side_effect = mock_ainvoke_side_effect
        mock_llm_class.return_value = mock_llm
        
        mock_prompt = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = mock_ainvoke_side_effect
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_template.return_value = mock_prompt
        
        builder = BuilderAgent()
        plan = {"requirements": {"type": "web_app"}}
        result = await builder.build(plan, 1)
        
        assert result["status"] == "success"
        assert "artifacts" in result
        assert len(result["artifacts"]) == 2  # test_main.py and main.py
        assert result["tool"] == "streamlit"  # Because type is web_app


@pytest.mark.asyncio
async def test_builder_build_syntax_error():
    """Test builder build method when generated code has syntax errors"""
    with patch('agents.builder.ChatOpenAI') as mock_llm_class, \
         patch('agents.builder.ChatPromptTemplate') as mock_prompt_class:
        
        # Mock the LLM to return code with syntax errors
        mock_llm = AsyncMock()
        mock_test_response = MagicMock()
        mock_test_response.content = "def test_function():\n    assert True\n"
        mock_impl_response = MagicMock()
        mock_impl_response.content = "def function():\n  return True\n  invalid_syntax"  # Syntax error
        
        call_count = 0
        def mock_ainvoke_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_test_response
            else:
                return mock_impl_response
        
        mock_llm.ainvoke.side_effect = mock_ainvoke_side_effect
        mock_llm_class.return_value = mock_llm
        
        mock_prompt = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = mock_ainvoke_side_effect
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_template.return_value = mock_prompt
        
        builder = BuilderAgent()
        plan = {"requirements": {"type": "python"}}
        result = await builder.build(plan, 1)
        
        # Should return retry due to validation failure
        assert result["status"] == "retry"


@pytest.mark.asyncio
async def test_builder_build_exception():
    """Test builder build method when exception occurs during build"""
    with patch('agents.builder.ChatOpenAI') as mock_llm_class, \
         patch('agents.builder.ChatPromptTemplate') as mock_prompt_class:
        
        # Mock the LLM to raise an exception
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM Error")
        mock_llm_class.return_value = mock_llm
        
        mock_prompt = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = Exception("LLM Error")
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_template.return_value = mock_prompt
        
        builder = BuilderAgent()
        plan = {"requirements": {"type": "python"}}
        result = await builder.build(plan, 1)
        
        assert result["status"] == "retry"  # Not at max iterations yet
        assert "error" in result


@pytest.mark.asyncio
async def test_builder_build_max_iterations():
    """Test builder build method reaches max iterations"""
    with patch('agents.builder.ChatOpenAI') as mock_llm_class, \
         patch('agents.builder.ChatPromptTemplate') as mock_prompt_class:
        
        # Mock the LLM to raise an exception
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM Error")
        mock_llm_class.return_value = mock_llm
        
        mock_prompt = MagicMock()
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = Exception("LLM Error")
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)
        mock_prompt_class.from_template.return_value = mock_prompt
        
        builder = BuilderAgent()
        plan = {"requirements": {"type": "python"}}
        result = await builder.build(plan, 10)  # At max iterations
        
        assert result["status"] == "fail"  # Should fail at max iterations
        assert "error" in result


def test_builder_select_tool_web_app():
    """Test _select_tool method for web app"""
    builder = BuilderAgent()
    plan = {"requirements": {"type": "web_app"}}
    tool = builder._select_tool(plan)
    assert tool == "streamlit"


def test_builder_select_tool_api():
    """Test _select_tool method for API"""
    builder = BuilderAgent()
    plan = {"requirements": {"type": "api"}}
    tool = builder._select_tool(plan)
    assert tool == "fastapi"


def test_builder_select_tool_mobile():
    """Test _select_tool method for mobile"""
    builder = BuilderAgent()
    plan = {"requirements": {"type": "mobile"}}
    tool = builder._select_tool(plan)
    assert tool == "pwa"


def test_builder_select_tool_extension():
    """Test _select_tool method for extension"""
    builder = BuilderAgent()
    plan = {"requirements": {"type": "extension"}}
    tool = builder._select_tool(plan)
    assert tool == "manifest_v3"


def test_builder_select_tool_default():
    """Test _select_tool method with unknown type (default)"""
    builder = BuilderAgent()
    plan = {"requirements": {"type": "unknown"}}
    tool = builder._select_tool(plan)
    assert tool == "python"


def test_builder_validate_code_valid():
    """Test _validate_code method with valid code"""
    builder = BuilderAgent()
    files = [
        {"name": "test_main.py", "content": "def test_func():\n    pass\n"},
        {"name": "main.py", "content": "def main():\n    pass\n"}
    ]
    is_valid = builder._validate_code(files)
    assert is_valid == True


def test_builder_validate_code_invalid():
    """Test _validate_code method with invalid code"""
    builder = BuilderAgent()
    files = [
        {"name": "main.py", "content": "def main():\n  invalid_syntax_here\n"}
    ]
    is_valid = builder._validate_code(files)
    assert is_valid == False


def test_builder_format_code_python():
    """Test _format_code method with Python files"""
    builder = BuilderAgent()
    files = [
        {"name": "main.py", "content": "def main  ():  pass"}
    ]
    formatted_files = builder._format_code(files)
    
    # The formatted content should be different from original if black processes it
    assert len(formatted_files) == 1
    assert formatted_files[0]["name"] == "main.py"