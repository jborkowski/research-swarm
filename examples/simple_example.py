#!/usr/bin/env python3
"""
Simple example of using the Research Swarm system
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from orchestrator.workflow import ResearchWorkflow
from utils.repository import RepositoryManager

async def main():
    print("Research Swarm System - Simple Example")
    print("=" * 50)
    
    # Create a simple idea
    idea = "Create a Python script that generates Fibonacci numbers"
    
    print(f"Processing idea: {idea}")
    print()
    
    # Initialize the workflow
    workflow = ResearchWorkflow()
    
    # Process the idea
    print("Starting research workflow...")
    result = await workflow.process_idea(idea, "example-001")
    
    # Display results
    print("\n" + "=" * 50)
    print("RESEARCH RESULTS")
    print("=" * 50)
    print(f"Status: {result.get('status', 'Unknown')}")
    print(f"Complexity: {result.get('complexity', 'Unknown')}")
    print(f"Summary: {result.get('summary', 'No summary')}")
    
    # Show generated artifacts
    artifacts = result.get('artifacts', [])
    if artifacts:
        print(f"\nGenerated {len(artifacts)} artifacts:")
        for artifact in artifacts:
            print(f"  - {artifact['name']}")
    
    # Show test results
    test_results = result.get('test_results', {})
    if test_results:
        print(f"\nTest Results:")
        print(f"  Unit Tests Passed: {test_results.get('unit_tests', {}).get('passed', False)}")
        print(f"  Coverage: {test_results.get('coverage', {}).get('percentage', 0)}%")
        print(f"  E2E Tests Passed: {test_results.get('e2e_tests', {}).get('passed', False)}")
    
    # Save to repository
    print("\nSaving to repository...")
    repo_manager = RepositoryManager("./example-output")
    idea_path = repo_manager.create_idea_folder("example-001", idea)
    
    if artifacts:
        repo_manager.save_implementation(idea_path, artifacts)
    
    if test_results:
        repo_manager.save_test_results(idea_path, test_results)
    
    repo_manager.finalize_idea(idea_path, result)
    
    print(f"Results saved to: {idea_path}")
    print("\nExample completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())