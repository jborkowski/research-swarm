import os
import tempfile
import subprocess
from typing import Dict, List, Optional
from pathlib import Path
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings

logger = logging.getLogger(__name__)


class BuilderAgent:
    """TDD-based implementation agent that generates working code."""

    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.2,
            model=settings.default_model,
            api_key=settings.openai_api_key
        )
        self.supported_languages = ["python", "javascript", "typescript"]

    async def build(self, plan: Dict, iteration: int = 1) -> Dict:
        """Build implementation following TDD methodology."""
        try:
            logger.info(f"Building implementation (iteration {iteration})")

            tool = self._select_tool(plan)
            logger.info(f"Selected tool/framework: {tool}")

            code_files = await self._generate_code_tdd(plan, tool, iteration)

            formatted_files = self._format_code(code_files)

            validation_result = await self._validate_code(formatted_files)

            if validation_result["valid"]:
                return {
                    "status": "success",
                    "artifacts": formatted_files,
                    "tool": tool,
                    "iteration": iteration,
                    "validation": validation_result
                }
            else:
                return {
                    "status": "retry" if iteration < settings.max_iterations else "fail",
                    "error": validation_result.get("error", "Code validation failed"),
                    "iteration": iteration,
                    "artifacts": formatted_files
                }

        except Exception as e:
            logger.error(f"Build failed: {e}")
            return {
                "status": "fail" if iteration >= settings.max_iterations else "retry",
                "error": str(e),
                "iteration": iteration
            }

    def _select_tool(self, plan: Dict) -> str:
        """Select the easiest/quickest tool for the job."""
        requirements = plan.get("requirements", {})
        req_type = requirements.get("type", "other")

        tool_matrix = {
            "web_app": "streamlit",
            "api": "fastapi",
            "mobile": "pwa",
            "extension": "manifest_v3",
            "script": "python",
            "data_processing": "python"
        }

        return tool_matrix.get(req_type, "python")

    async def _generate_code_tdd(self, plan: Dict, tool: str, iteration: int) -> List[Dict]:
        """Generate code following TDD: tests first, then implementation."""

        test_prompt = ChatPromptTemplate.from_template("""
You are an expert test-driven development engineer.

Plan:
{plan}

Framework/Tool: {tool}
Iteration: {iteration}

Generate comprehensive test files that cover the core functionality described in the plan.

For Python (pytest):
- Create test_main.py with pytest test cases
- Use fixtures appropriately
- Test edge cases and error conditions
- Follow pytest best practices

For JavaScript (jest):
- Create main.test.js with jest test cases
- Use proper mocking
- Test edge cases and error conditions

Provide ONLY the test code, no explanations. Start with the file name as a comment.
Generate complete, runnable tests.
""")

        impl_prompt = ChatPromptTemplate.from_template("""
You are an expert software engineer implementing code to pass tests.

Tests:
{tests}

Plan:
{plan}

Framework/Tool: {tool}

Generate the minimal implementation code that passes these tests.

For Python:
- Create main.py or appropriate module
- Use type hints
- Follow PEP 8
- Keep it simple and focused

For JavaScript:
- Create main.js or appropriate module
- Use modern ES6+ syntax
- Follow best practices

Provide ONLY the implementation code, no explanations. Start with the file name as a comment.
Generate complete, runnable code that makes the tests pass.
""")

        chain_test = test_prompt | self.llm
        test_response = await chain_test.ainvoke({
            "plan": str(plan),
            "tool": tool,
            "iteration": iteration
        })

        chain_impl = impl_prompt | self.llm
        impl_response = await chain_impl.ainvoke({
            "tests": test_response.content,
            "plan": str(plan),
            "tool": tool
        })

        files = []

        if tool in ["python", "fastapi", "streamlit"]:
            files.append({
                "name": "test_main.py",
                "content": self._extract_code(test_response.content),
                "type": "test"
            })
            files.append({
                "name": "main.py",
                "content": self._extract_code(impl_response.content),
                "type": "implementation"
            })
            files.append({
                "name": "requirements.txt",
                "content": self._generate_requirements(tool),
                "type": "dependency"
            })
        else:
            files.append({
                "name": "main.test.js",
                "content": self._extract_code(test_response.content),
                "type": "test"
            })
            files.append({
                "name": "main.js",
                "content": self._extract_code(impl_response.content),
                "type": "implementation"
            })
            files.append({
                "name": "package.json",
                "content": self._generate_package_json(tool),
                "type": "dependency"
            })

        files.append({
            "name": "README.md",
            "content": self._generate_readme(plan, tool),
            "type": "documentation"
        })

        return files

    def _extract_code(self, content: str) -> str:
        """Extract code from LLM response, removing markdown formatting."""
        lines = content.strip().split("\n")
        code_lines = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block or not line.strip().startswith("#"):
                code_lines.append(line)

        return "\n".join(code_lines).strip()

    def _format_code(self, files: List[Dict]) -> List[Dict]:
        """Format code using language-specific formatters."""
        formatted = []

        for file in files:
            content = file["content"]

            if file["name"].endswith(".py"):
                try:
                    import black
                    content = black.format_str(content, mode=black.Mode())
                except Exception as e:
                    logger.warning(f"Black formatting failed: {e}")
                    try:
                        import autopep8
                        content = autopep8.fix_code(content)
                    except Exception as e2:
                        logger.warning(f"Autopep8 formatting failed: {e2}")

            elif file["name"].endswith(".js"):
                pass

            formatted.append({
                **file,
                "content": content
            })

        return formatted

    async def _validate_code(self, files: List[Dict]) -> Dict:
        """Validate code syntax and basic structure."""
        errors = []

        for file in files:
            if file["name"].endswith(".py"):
                try:
                    compile(file["content"], file["name"], "exec")
                except SyntaxError as e:
                    errors.append(f"{file['name']}: {str(e)}")

        if errors:
            return {
                "valid": False,
                "errors": errors,
                "error": "; ".join(errors)
            }

        return {
            "valid": True,
            "errors": [],
            "message": "Code validation passed"
        }

    def _generate_requirements(self, tool: str) -> str:
        """Generate requirements.txt based on tool selection."""
        base_requirements = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0"
        ]

        tool_requirements = {
            "streamlit": ["streamlit>=1.28.0"],
            "fastapi": ["fastapi>=0.104.0", "uvicorn>=0.24.0", "pydantic>=2.0.0"],
            "python": []
        }

        requirements = base_requirements + tool_requirements.get(tool, [])
        return "\n".join(requirements)

    def _generate_package_json(self, tool: str) -> str:
        """Generate package.json for JavaScript projects."""
        import json

        package = {
            "name": "generated-project",
            "version": "1.0.0",
            "scripts": {
                "test": "jest",
                "start": "node main.js"
            },
            "devDependencies": {
                "jest": "^29.0.0"
            },
            "dependencies": {}
        }

        return json.dumps(package, indent=2)

    def _generate_readme(self, plan: Dict, tool: str) -> str:
        """Generate README documentation."""
        overview = plan.get("overview", "Generated implementation")

        return f"""# {overview}

## Overview
This is an auto-generated implementation based on the research swarm analysis.

## Technology Stack
- Framework: {tool}

## Setup

### Python
```bash
pip install -r requirements.txt
```

### JavaScript
```bash
npm install
```

## Running

### Python
```bash
python main.py
```

### JavaScript
```bash
npm start
```

## Testing

### Python
```bash
pytest
```

### JavaScript
```bash
npm test
```

## Implementation Details
{plan.get('reasoning', 'See plan for details')}
"""
