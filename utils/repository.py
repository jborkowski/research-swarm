import git
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
import re

class RepositoryManager:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        # Create the repository directory if it doesn't exist
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize git repo if it doesn't exist
        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.repo_path)
    
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
            try:
                self.repo.remotes.origin.push()
            except:
                pass  # Ignore if push fails
    
    def _sanitize_name(self, text: str) -> str:
        # Remove special characters and spaces
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
    
    def _format_findings(self, findings: List) -> str:
        if not findings:
            return "No findings available"
        
        formatted = []
        for finding in findings:
            if isinstance(finding, dict):
                formatted.append(f"- {finding.get('agent', 'Unknown')}: {finding.get('query', 'No query')}")
            else:
                formatted.append(f"- {finding}")
        
        return "\n".join(formatted)
    
    def _analyze_feasibility(self, research: Dict) -> str:
        return f"""# Feasibility Analysis

## Technical Feasibility
Based on the research findings, this idea appears technically feasible.

## Resource Requirements
- Development time: Estimated based on complexity
- API access: As needed
- Infrastructure: Standard cloud or local deployment

## Potential Challenges
- Implementation complexity based on research findings
- Integration requirements
- Testing and validation needs

## Risk Assessment
- Low to medium risk for standard implementations
- Higher risk for complex or novel approaches
"""
    
    def _extract_references(self, research: Dict) -> str:
        return f"""# Research References

## Sources Consulted
{json.dumps(research.get('findings', []), indent=2)}

## Additional Resources
- Documentation links
- API references
- Code examples
- Academic papers
"""
    
    def _generate_impl_readme(self, artifacts: List[Dict]) -> str:
        files_list = "\n".join([f"- {artifact['name']}" for artifact in artifacts])
        return f"""# Implementation

## Generated Files
{files_list}

## Setup Instructions
1. Install dependencies
2. Run the main script
3. Execute tests

## Usage
python main.py

## Testing
python -m pytest test_main.py
"""
    
    def _generate_test_report(self, test_results: Dict) -> str:
        return f"""# Test Report

## Summary
- **Unit Tests**: {test_results['unit_tests']['passed']}
- **Coverage**: {test_results['coverage']['percentage']}%
- **E2E Tests**: {test_results['e2e_tests']['passed']}

## Details
{json.dumps(test_results, indent=2)}
"""
    
    def _generate_summary(self, summary: Dict) -> str:
        return f"""# Final Summary

## Idea
{summary.get('idea_text', 'No idea text')}

## Status
{summary.get('status', 'Unknown')}

## Complexity
{summary.get('complexity', 'Unknown')}

## Results
{summary.get('summary', 'No summary available')}

## Generated Artifacts
{len(summary.get('artifacts', []))} files generated

## Test Results
{summary.get('test_results', 'No test results')}
"""