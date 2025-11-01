import git
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
import logging
import re

logger = logging.getLogger(__name__)


class RepositoryManager:
    """Manages the research output repository structure and Git operations."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = self._init_repository()

    def _init_repository(self) -> git.Repo:
        """Initialize or open Git repository."""
        try:
            if self.repo_path.exists() and (self.repo_path / ".git").exists():
                repo = git.Repo(self.repo_path)
                logger.info(f"Opened existing repository at {self.repo_path}")
            else:
                self.repo_path.mkdir(parents=True, exist_ok=True)
                repo = git.Repo.init(self.repo_path)
                logger.info(f"Initialized new repository at {self.repo_path}")

                (self.repo_path / "README.md").write_text(
                    "# Research Swarm Output Repository\n\n"
                    "This repository contains research and implementation outputs "
                    "from the Research Swarm system.\n"
                )
                repo.index.add(["README.md"])
                repo.index.commit("Initial commit")

            return repo
        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            raise

    def create_idea_folder(self, idea_id: str, idea_text: str) -> Path:
        """Create a new folder structure for an idea."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        safe_name = self._sanitize_name(idea_text[:50])
        folder_name = f"{timestamp}-{safe_name}"

        idea_path = self.repo_path / "ideas" / folder_name
        idea_path.mkdir(parents=True, exist_ok=True)

        metadata = {
            "idea_id": idea_id,
            "idea_text": idea_text,
            "folder_name": folder_name,
            "created_at": datetime.now().isoformat(),
            "status": "processing",
            "phases": []
        }

        (idea_path / "metadata.json").write_text(
            json.dumps(metadata, indent=2)
        )

        for subdir in ["research", "plan", "implementation", "results"]:
            (idea_path / subdir).mkdir(exist_ok=True)

        try:
            self.repo.index.add([str(idea_path / "metadata.json")])
            self.repo.index.commit(f"Initialize idea: {safe_name}")
            logger.info(f"Created idea folder: {folder_name}")
        except Exception as e:
            logger.warning(f"Failed to commit idea folder: {e}")

        return idea_path

    def save_research(self, idea_path: Path, research: Dict):
        """Save research results."""
        research_path = idea_path / "research"

        readme = self._generate_research_readme(research)
        (research_path / "README.md").write_text(readme)

        (research_path / "research_data.json").write_text(
            json.dumps(research, indent=2)
        )

        feasibility = self._analyze_feasibility(research)
        (research_path / "feasibility.md").write_text(feasibility)

        try:
            self.repo.index.add([str(research_path)])
            self.repo.index.commit(f"Add research for {idea_path.name}")
            logger.info("Research saved and committed")
        except Exception as e:
            logger.warning(f"Failed to commit research: {e}")

    def save_plan(self, idea_path: Path, plan: Dict):
        """Save implementation plan."""
        plan_path = idea_path / "plan"

        (plan_path / "plan.json").write_text(
            json.dumps(plan, indent=2)
        )

        plan_md = self._generate_plan_markdown(plan)
        (plan_path / "implementation_plan.md").write_text(plan_md)

        try:
            self.repo.index.add([str(plan_path)])
            self.repo.index.commit(f"Add plan for {idea_path.name}")
            logger.info("Plan saved and committed")
        except Exception as e:
            logger.warning(f"Failed to commit plan: {e}")

    def save_implementation(self, idea_path: Path, artifacts: List[Dict]):
        """Save implementation artifacts."""
        impl_path = idea_path / "implementation"
        src_path = impl_path / "src"
        src_path.mkdir(exist_ok=True)

        for artifact in artifacts:
            if artifact.get("type") == "test":
                file_path = impl_path / "tests" / artifact["name"]
                file_path.parent.mkdir(exist_ok=True)
            elif artifact.get("type") == "dependency":
                file_path = impl_path / artifact["name"]
            elif artifact.get("type") == "documentation":
                file_path = impl_path / artifact["name"]
            else:
                file_path = src_path / artifact["name"]

            file_path.write_text(artifact["content"])

        readme = self._generate_impl_readme(artifacts)
        (impl_path / "README.md").write_text(readme)

        try:
            self.repo.index.add([str(impl_path)])
            self.repo.index.commit(f"Add implementation for {idea_path.name}")
            logger.info("Implementation saved and committed")
        except Exception as e:
            logger.warning(f"Failed to commit implementation: {e}")

    def save_test_results(self, idea_path: Path, test_results: Dict):
        """Save test results."""
        results_path = idea_path / "results"

        report = self._generate_test_report(test_results)
        (results_path / "test-report.md").write_text(report)

        (results_path / "test-results.json").write_text(
            json.dumps(test_results, indent=2)
        )

        try:
            self.repo.index.add([str(results_path)])
            self.repo.index.commit(f"Add test results for {idea_path.name}")
            logger.info("Test results saved and committed")
        except Exception as e:
            logger.warning(f"Failed to commit test results: {e}")

    def finalize_idea(self, idea_path: Path, summary: Dict):
        """Finalize idea processing and update metadata."""
        metadata_path = idea_path / "metadata.json"
        metadata = json.loads(metadata_path.read_text())

        metadata["status"] = summary.get("status", "completed")
        metadata["completed_at"] = datetime.now().isoformat()
        metadata["summary"] = summary

        metadata_path.write_text(json.dumps(metadata, indent=2))

        summary_text = self._generate_summary(summary)
        (idea_path / "SUMMARY.md").write_text(summary_text)

        try:
            self.repo.index.add([str(idea_path)])
            self.repo.index.commit(f"Complete processing for {idea_path.name}")

            if self.repo.remotes:
                try:
                    self.repo.remotes.origin.push()
                    logger.info("Changes pushed to remote")
                except Exception as e:
                    logger.warning(f"Failed to push to remote: {e}")

            logger.info("Idea finalized")
        except Exception as e:
            logger.warning(f"Failed to commit finalization: {e}")

    def _sanitize_name(self, text: str) -> str:
        """Create a safe filename from text."""
        safe = re.sub(r'[^\w\s-]', '', text.lower())
        safe = re.sub(r'[-\s]+', '-', safe)
        return safe[:50].strip('-')

    def _generate_research_readme(self, research: Dict) -> str:
        """Generate research summary README."""
        synthesis = research.get("synthesis", {})

        return f"""# Research Summary

## Overview
{synthesis.get('synthesis', 'Research completed')}

## Feasibility
- **Feasible**: {synthesis.get('feasible', 'Unknown')}
- **Confidence**: {synthesis.get('confidence', 0):.0%}

## Key Findings
{self._format_findings(research.get('results', []))}

## Recommendations
{self._format_list(synthesis.get('recommendations', []))}

## Identified Blockers
{self._format_list(synthesis.get('blockers', []))}

## Technical Approach
{synthesis.get('technical_approach', 'See detailed plan')}

---
*Generated by Research Swarm*
"""

    def _generate_plan_markdown(self, plan: Dict) -> str:
        """Generate plan documentation."""
        return f"""# Implementation Plan

## Overview
{plan.get('overview', 'Implementation plan')}

## Complexity Assessment
- **Complexity**: {plan.get('complexity', 'Unknown')}
- **Estimated Effort**: {plan.get('estimated_effort_minutes', 60)} minutes

## Requirements
{json.dumps(plan.get('requirements', {}), indent=2)}

## Dependencies
{self._format_list(plan.get('dependencies', []))}

## Tasks
{self._format_tasks(plan.get('tasks', []))}

---
*Generated by Research Swarm*
"""

    def _generate_impl_readme(self, artifacts: List[Dict]) -> str:
        """Generate implementation README."""
        return f"""# Implementation

## Files Generated
{self._format_artifacts(artifacts)}

## Setup Instructions

### Install Dependencies
```bash
# Python
pip install -r requirements.txt

# JavaScript
npm install
```

### Run Tests
```bash
# Python
pytest

# JavaScript
npm test
```

### Run Application
```bash
# Python
python src/main.py

# JavaScript
npm start
```

---
*Generated by Research Swarm*
"""

    def _generate_test_report(self, test_results: Dict) -> str:
        """Generate test report."""
        unit_tests = test_results.get('unit_tests', {})
        coverage = test_results.get('coverage', {})

        return f"""# Test Report

## Summary
- **Overall Status**: {'PASSED' if test_results.get('passed') else 'FAILED'}
- **Unit Tests**: {unit_tests.get('status', 'Unknown')}
- **Coverage**: {coverage.get('percentage', 0)}%

## Unit Tests
**Status**: {unit_tests.get('status', 'Unknown')}
**Passed**: {'Yes' if unit_tests.get('passed') else 'No'}

### Output
```
{unit_tests.get('output', 'No output available')}
```

## Coverage Analysis
- **Percentage**: {coverage.get('percentage', 0)}%
- **Meets Threshold (70%)**: {'Yes' if coverage.get('meets_threshold') else 'No'}

## Details
{test_results.get('summary', 'No additional details')}

---
*Generated by Research Swarm*
"""

    def _generate_summary(self, summary: Dict) -> str:
        """Generate final summary."""
        return f"""# Project Summary

## Status
{summary.get('status', 'Unknown')}

## Timeline
- **Started**: {summary.get('started_at', 'Unknown')}
- **Completed**: {summary.get('completed_at', 'Unknown')}

## Results
{summary.get('message', 'Processing complete')}

## Key Outcomes
{self._format_dict(summary.get('outcomes', {}))}

---
*Generated by Research Swarm on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _analyze_feasibility(self, research: Dict) -> str:
        """Analyze and document feasibility."""
        synthesis = research.get("synthesis", {})

        return f"""# Feasibility Analysis

## Assessment
**Feasible**: {synthesis.get('feasible', 'Unknown')}
**Confidence**: {synthesis.get('confidence', 0):.0%}

## Reasoning
{synthesis.get('synthesis', 'No analysis available')}

## Blockers
{self._format_list(synthesis.get('blockers', []))}

## Recommendations
{self._format_list(synthesis.get('recommendations', []))}

---
*Generated by Research Swarm*
"""

    def _format_findings(self, findings: List) -> str:
        """Format research findings."""
        if not findings:
            return "No findings available"

        lines = []
        for i, finding in enumerate(findings, 1):
            if isinstance(finding, dict):
                lines.append(f"\n### Finding {i}: {finding.get('agent', 'Unknown')}")
                lines.append(finding.get('summary', 'No summary'))
            else:
                lines.append(f"\n### Finding {i}")
                lines.append(str(finding))

        return "\n".join(lines)

    def _format_list(self, items: List) -> str:
        """Format a list as markdown."""
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)

    def _format_tasks(self, tasks: List) -> str:
        """Format tasks as markdown."""
        if not tasks:
            return "No tasks defined"

        lines = []
        for i, task in enumerate(tasks, 1):
            if isinstance(task, dict):
                lines.append(f"\n### Task {i}: {task.get('description', 'Unknown')}")
                lines.append(f"- **Priority**: {task.get('priority', 'N/A')}")
                lines.append(f"- **Estimated Time**: {task.get('estimated_time', 'N/A')}")
            else:
                lines.append(f"\n### Task {i}")
                lines.append(str(task))

        return "\n".join(lines)

    def _format_artifacts(self, artifacts: List[Dict]) -> str:
        """Format artifacts list."""
        lines = []
        for artifact in artifacts:
            lines.append(f"- `{artifact['name']}` ({artifact.get('type', 'unknown')})")
        return "\n".join(lines) if lines else "No artifacts"

    def _format_dict(self, data: Dict) -> str:
        """Format dictionary as markdown."""
        if not data:
            return "No data available"

        lines = []
        for key, value in data.items():
            lines.append(f"- **{key}**: {value}")

        return "\n".join(lines)
