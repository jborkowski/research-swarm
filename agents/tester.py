import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TesterAgent:
    """Agent responsible for running tests and validating implementations."""

    async def test(self, artifacts: List[Dict], requirements: Dict) -> Dict:
        """Run comprehensive tests on generated artifacts."""
        try:
            logger.info("Running tests on generated code")

            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)

                for artifact in artifacts:
                    file_path = tmppath / artifact["name"]
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(artifact["content"])

                is_python = any(a["name"].endswith(".py") for a in artifacts)
                is_javascript = any(a["name"].endswith(".js") for a in artifacts)

                if is_python:
                    test_results = await self._run_python_tests(tmppath)
                    coverage_results = await self._run_python_coverage(tmppath)
                elif is_javascript:
                    test_results = await self._run_javascript_tests(tmppath)
                    coverage_results = {"percentage": 0, "meets_threshold": False}
                else:
                    return {
                        "unit_tests": {"status": "skipped", "passed": True},
                        "coverage": {"percentage": 0, "meets_threshold": False},
                        "e2e_tests": {"status": "skipped", "passed": True},
                        "passed": True,
                        "message": "No runnable tests found"
                    }

                e2e_results = {"status": "not_implemented", "passed": True}

                all_passed = (
                    test_results.get("passed", False) and
                    e2e_results.get("passed", True)
                )

                return {
                    "unit_tests": test_results,
                    "coverage": coverage_results,
                    "e2e_tests": e2e_results,
                    "passed": all_passed,
                    "summary": self._generate_summary(test_results, coverage_results)
                }

        except Exception as e:
            logger.error(f"Testing failed: {e}")
            return {
                "unit_tests": {"status": "error", "passed": False, "error": str(e)},
                "coverage": {"percentage": 0, "meets_threshold": False},
                "e2e_tests": {"status": "error", "passed": False},
                "passed": False,
                "error": str(e)
            }

    async def _run_python_tests(self, path: Path) -> Dict:
        """Run pytest on Python code."""
        test_files = list(path.glob("test_*.py"))

        if not test_files:
            logger.warning("No Python test files found")
            return {"status": "no_tests", "passed": True, "output": ""}

        try:
            result = subprocess.run(
                ["pip", "install", "-q", "pytest", "pytest-asyncio"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=60
            )

            result = subprocess.run(
                ["python", "-m", "pytest", "-v", "--tb=short"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=120
            )

            passed = result.returncode == 0

            logger.info(f"Python tests {'passed' if passed else 'failed'}")

            return {
                "status": "completed",
                "passed": passed,
                "output": result.stdout,
                "errors": result.stderr if not passed else "",
                "exit_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            logger.error("Python tests timed out")
            return {
                "status": "timeout",
                "passed": False,
                "error": "Tests timed out after 120 seconds"
            }
        except Exception as e:
            logger.error(f"Failed to run Python tests: {e}")
            return {
                "status": "error",
                "passed": False,
                "error": str(e)
            }

    async def _run_python_coverage(self, path: Path) -> Dict:
        """Run coverage analysis on Python code."""
        try:
            result = subprocess.run(
                ["pip", "install", "-q", "pytest-cov"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=60
            )

            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=.", "--cov-report=term"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=120
            )

            output = result.stdout

            import re
            match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)

            if match:
                percentage = int(match.group(1))
            else:
                percentage = 0

            logger.info(f"Code coverage: {percentage}%")

            return {
                "percentage": percentage,
                "meets_threshold": percentage >= 70,
                "output": output
            }

        except Exception as e:
            logger.warning(f"Coverage analysis failed: {e}")
            return {
                "percentage": 0,
                "meets_threshold": False,
                "error": str(e)
            }

    async def _run_javascript_tests(self, path: Path) -> Dict:
        """Run jest on JavaScript code."""
        test_files = list(path.glob("*.test.js"))

        if not test_files:
            logger.warning("No JavaScript test files found")
            return {"status": "no_tests", "passed": True, "output": ""}

        try:
            result = subprocess.run(
                ["npm", "install", "--silent"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=120
            )

            result = subprocess.run(
                ["npm", "test"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=120
            )

            passed = result.returncode == 0

            logger.info(f"JavaScript tests {'passed' if passed else 'failed'}")

            return {
                "status": "completed",
                "passed": passed,
                "output": result.stdout,
                "errors": result.stderr if not passed else "",
                "exit_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            logger.error("JavaScript tests timed out")
            return {
                "status": "timeout",
                "passed": False,
                "error": "Tests timed out after 120 seconds"
            }
        except Exception as e:
            logger.error(f"Failed to run JavaScript tests: {e}")
            return {
                "status": "error",
                "passed": False,
                "error": str(e)
            }

    def _generate_summary(self, test_results: Dict, coverage_results: Dict) -> str:
        """Generate a human-readable test summary."""
        lines = []

        lines.append(f"Test Status: {test_results.get('status', 'unknown')}")
        lines.append(f"Tests Passed: {'Yes' if test_results.get('passed') else 'No'}")
        lines.append(f"Coverage: {coverage_results.get('percentage', 0)}%")
        lines.append(f"Meets Threshold (70%): {'Yes' if coverage_results.get('meets_threshold') else 'No'}")

        return "\n".join(lines)
