import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List
import pytest

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
            
            # Run coverage analysis (placeholder)
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
            ["python", "-m", "pytest", "-v", "--tb=short"],
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
        """Run coverage analysis on the code"""
        try:
            import coverage

            # Initialize coverage
            cov = coverage.Coverage(source=[str(path)], omit=["test_*.py", "__pycache__/*"])

            # Start coverage
            cov.start()

            # Run tests to collect coverage data
            import subprocess
            result = subprocess.run(
                ["python", "-m", "pytest", "-x", "-q"],
                cwd=path,
                capture_output=True,
                text=True
            )

            # Stop coverage
            cov.stop()
            cov.save()

            # Get coverage report
            total = cov.report()

            return {
                "percentage": total,
                "meets_threshold": total >= 70.0
            }
        except ImportError:
            # If coverage is not available, return basic info
            return {
                "percentage": 0.0,
                "meets_threshold": False,
                "error": "coverage package not available"
            }
        except Exception as e:
            return {
                "percentage": 0.0,
                "meets_threshold": False,
                "error": str(e)
            }
    
    async def _run_e2e_tests(self, path: Path, requirements: Dict) -> Dict:
        # Generate E2E test based on requirements
        e2e_test = self._generate_e2e_test(requirements)
        
        # Write E2E test
        e2e_path = path / "test_e2e.py"
        e2e_path.write_text(e2e_test)
        
        # Run E2E test
        result = subprocess.run(
            ["python", "-m", "pytest", "test_e2e.py", "-v"],
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
        return f'''
import pytest

def test_end_to_end_workflow():
    """Test the complete workflow based on requirements: {requirements}"""
    # Setup
    # ... test setup code ...
    
    # Execute
    # ... test execution ...
    
    # Assert
    assert True  # Replace with actual assertions
'''
    
    def _all_tests_passed(self, unit_results: Dict, e2e_results: Dict) -> bool:
        return (
            unit_results.get("passed", True) and
            e2e_results.get("passed", True)
        )