import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from agents.tester import TesterAgent


@pytest.mark.asyncio
async def test_tester_test_success():
    """Test tester test method with successful test run"""
    with patch('agents.tester.subprocess') as mock_subprocess:
        # Mock subprocess.run to return a successful result
        mock_result = MagicMock()
        mock_result.returncode = 0  # Success
        mock_result.stdout = "Tests passed"
        mock_result.stderr = ""
        mock_subprocess.run.return_value = mock_result
        
        tester = TesterAgent()
        artifacts = [
            {"name": "test_main.py", "content": "def test_func():\n    assert True\n"},
            {"name": "main.py", "content": "def main():\n    return True\n"}
        ]
        requirements = {"test": "requirements"}
        
        result = await tester.test(artifacts, requirements)
        
        assert result["unit_tests"]["passed"] == True
        assert result["coverage"]["meets_threshold"] == False  # Default value
        assert result["e2e_tests"]["passed"] == True  # Default if no errors
        assert result["passed"] == True


@pytest.mark.asyncio
async def test_tester_test_failure():
    """Test tester test method with test failure"""
    with patch('agents.tester.subprocess') as mock_subprocess:
        # Mock subprocess.run to return a failure result
        mock_result = MagicMock()
        mock_result.returncode = 1  # Failure
        mock_result.stdout = "Tests failed"
        mock_result.stderr = "Error details"
        mock_subprocess.run.return_value = mock_result
        
        tester = TesterAgent()
        artifacts = [
            {"name": "test_main.py", "content": "def test_func():\n    assert False\n"}
        ]
        requirements = {"test": "requirements"}
        
        result = await tester.test(artifacts, requirements)
        
        assert result["unit_tests"]["passed"] == False
        assert result["e2e_tests"]["passed"] == False
        assert result["passed"] == False


def test_all_tests_passed_both_true():
    """Test _all_tests_passed method with both tests passing"""
    tester = TesterAgent()
    unit_results = {"passed": True}
    e2e_results = {"passed": True}
    
    result = tester._all_tests_passed(unit_results, e2e_results)
    assert result == True


def test_all_tests_passed_unit_false():
    """Test _all_tests_passed method with unit test failing"""
    tester = TesterAgent()
    unit_results = {"passed": False}
    e2e_results = {"passed": True}
    
    result = tester._all_tests_passed(unit_results, e2e_results)
    assert result == False


def test_all_tests_passed_e2e_false():
    """Test _all_tests_passed method with E2E test failing"""
    tester = TesterAgent()
    unit_results = {"passed": True}
    e2e_results = {"passed": False}
    
    result = tester._all_tests_passed(unit_results, e2e_results)
    assert result == False


def test_all_tests_passed_both_false():
    """Test _all_tests_passed method with both tests failing"""
    tester = TesterAgent()
    unit_results = {"passed": False}
    e2e_results = {"passed": False}
    
    result = tester._all_tests_passed(unit_results, e2e_results)
    assert result == False


def test_all_tests_passed_defaults():
    """Test _all_tests_passed method with default values"""
    tester = TesterAgent()
    unit_results = {}
    e2e_results = {}
    
    result = tester._all_tests_passed(unit_results, e2e_results)
    assert result == True  # Default to True if not specified


@pytest.mark.asyncio
async def test_tester_run_tests_no_test_files():
    """Test _run_tests method when no test files exist"""
    tester = TesterAgent()
    
    # Create a temporary directory with no test files
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # No test files created
        result = await tester._run_tests(tmppath)
        
        assert result["status"] == "no_tests"
        assert result["passed"] == True  # No tests means no failures


@pytest.mark.asyncio
async def test_tester_run_coverage():
    """Test _run_coverage method"""
    tester = TesterAgent()
    
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create a dummy test file
        (tmppath / "test_dummy.py").write_text("def test_dummy():\n    assert True\n")
        
        result = await tester._run_coverage(tmppath)
        
        # The result should have percentage and meets_threshold
        assert "percentage" in result
        assert "meets_threshold" in result


@pytest.mark.asyncio
async def test_tester_run_e2e_tests():
    """Test _run_e2e_tests method"""
    tester = TesterAgent()
    
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create a dummy main file
        (tmppath / "main.py").write_text("def main():\n    return 'Hello World'\n")
        
        requirements = {"test": "requirements"}
        result = await tester._run_e2e_tests(tmppath, requirements)
        
        # Should have a passed status and output
        assert "passed" in result
        assert "output" in result


def test_tester_generate_e2e_test():
    """Test _generate_e2e_test method"""
    tester = TesterAgent()
    requirements = {"feature": "test feature"}
    
    e2e_test = tester._generate_e2e_test(requirements)
    
    # Should contain the requirements string
    assert "test feature" in e2e_test
    assert "def test_end_to_end_workflow" in e2e_test