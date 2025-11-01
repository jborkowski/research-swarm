import git
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List

class RepositoryManager:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(self.repo_path)
    
    def create_idea_folder(self, idea_id: str, idea_text: str) -> Path:
        # Create folder with timestamp and sanitized name
        timestamp = datetime.now().strftime("%Y-%m-%d")
        safe_name = self._sanitize_name(idea_text[:50])
        folder_name = f"{timestamp}-{safe_name}"
        
        idea_path = self.repo_path / "ideas" / folder_name
        idea_path.mkdir(parents=True, exist_ok=True)
        
        # Create metadata file
        metadata = {
            "idea_id": idea_id,
            "idea_text": idea_text,
            "created_at": datetime.now().isoformat(),
            "status": "processing"
        }
        
        (idea_path / "metadata.json").write_text(
            json.dumps(metadata, indent=2)
        )
        
        # Create subdirectories
        for subdir in ["research", "plan", "implementation", "results"]:
            (idea_path / subdir).mkdir(exist_ok=True)
        
        # Initial commit
        self.repo.index.add([str(idea_path)])
        self.repo.index.commit(f"Initialize idea: {safe_name}")
        
        return idea_path
    
    def save_research(self, idea_path: Path, research: Dict):
        research_path = idea_path / "research"
        
        # Save main research document
        readme = self._generate_research_readme(research)
        (research_path / "README.md").write_text(readme)
        
        # Save feasibility analysis
        feasibility = self._analyze_feasibility(research)
        (research_path / "feasibility.md").write_text(feasibility)
        
        # Save references
        refs = self._extract_references(research)
        (research_path / "references.md").write_text(refs)
        
        # Commit
        self.repo.index.add([str(research_path)])
        self.repo.index.commit(f"Add research for {idea_path.name}")
    
    def save_implementation(self, idea_path: Path, artifacts: List[Dict]):
        impl_path = idea_path / "implementation"
        
        for artifact in artifacts:
            file_path = impl_path / artifact["name"]
            file_path.write_text(artifact["content"])
        
        # Create README
        readme = self._generate_impl_readme(artifacts)
        (impl_path / "README.md").write_text(readme)
        
        # Commit
        self.repo.index.add([str(impl_path)])
        self.repo.index.commit(f"Add implementation for {idea_path.name}")
    
    def save_test_results(self, idea_path: Path, test_results: Dict):
        results_path = idea_path / "results"
        
        # Save test report
        report = self._generate_test_report(test_results)
        (results_path / "test-report.md").write_text(report)
        
        # Save coverage if available
        if "coverage" in test_results:
            (results_path / "coverage.json").write_text(
                json.dumps(test_results["coverage"], indent=2)
            )
        
        # Commit
        self.repo.index.add([str(results_path)])
        self.repo.index.commit(f"Add test results for {idea_path.name}")
    
    def finalize_idea(self, idea_path: Path, summary: Dict):
        # Update metadata
        metadata_path = idea_path / "metadata.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["status"] = "completed"
        metadata["completed_at"] = datetime.now().isoformat()
        metadata["summary"] = summary
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        # Create final summary
        summary_text = self._generate_summary(summary)
        (idea_path / "SUMMARY.md").write_text(summary_text)
        
        # Final commit
        self.repo.index.add([str(idea_path)])
        self.repo.index.commit(f"Complete processing for {idea_path.name}")
        
        # Push to remote if configured
        if self.repo.remotes:
            self.repo.remotes.origin.push()
    
    def _sanitize_name(self, text: str) -> str:
        # Remove special characters and spaces
        import re
        safe = re.sub(r'[^\w\s-]', '', text.lower())
        safe = re.sub(r'[-\s]+', '-', safe)
        return safe[:50]
    
    def _generate_research_readme(self, research: Dict) -> str:
        return f"""# Research Summary

## Overview
{research.get('overview', 'No overview available')}

## Key Findings
{self._format_findings(research.get('findings', []))}

## Technical Analysis
{research.get('technical_analysis', 'No analysis available')}

## Recommendations
{research.get('recommendations', 'No recommendations')}

## Next Steps
{research.get('next_steps', 'No next steps defined')}
"""
    
    def _format_findings(self, findings: List[Dict]) -> str:
        result = ""
        for i, finding in enumerate(findings, 1):
            result += f"{i}. {finding.get('content', 'No content')}\n\n"
        return result
    
    def _analyze_feasibility(self, research: Dict) -> str:
        return f"""# Feasibility Analysis

## Technical Feasibility
Based on the research, the technical feasibility is assessed.

## Resource Requirements
Estimate of resources needed for implementation.

## Timeline Estimate
Estimated time to complete the implementation.

## Risk Assessment
Potential risks and mitigation strategies.
"""
    
    def _extract_references(self, research: Dict) -> str:
        return f"""# References

## Sources
List of sources and references used in the research.
"""
    
    def _generate_impl_readme(self, artifacts: List[Dict]) -> str:
        return f"""# Implementation

## Files Generated
{len(artifacts)} files generated

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python main.py`

## Files
{', '.join([a['name'] for a in artifacts])}
"""
    
    def _generate_test_report(self, test_results: Dict) -> str:
        return f"""# Test Report

## Summary
- **Unit Tests**: {test_results['unit_tests']['passed']}
- **Coverage**: {test_results['coverage'].get('percentage', 0)}%
- **E2E Tests**: {test_results['e2e_tests']['passed']}

## Details
{json.dumps(test_results, indent=2)}
"""
    
    def _generate_summary(self, summary: Dict) -> str:
        return f"""# Final Summary

## Result
{summary.get('summary', 'No summary available')}

## Research Results
{summary.get('research_results', 'No research results')}

## Implementation
{summary.get('implementation', 'No implementation')}

## Test Results
{summary.get('test_results', 'No test results')}
"""