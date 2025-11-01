#!/usr/bin/env python3
"""
Research Swarm System Demo
==========================

This demo shows the complete Research Swarm system in action,
processing ideas through the full automated workflow.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.workflow import ResearchWorkflow

async def demo():
    print("🤖 Research Swarm System Demo")
    print("=" * 50)
    
    # Initialize the workflow
    workflow = ResearchWorkflow()
    
    # Test ideas of different complexities
    test_ideas = [
        "Create a Python script that calculates factorial",
        "Build a web scraper that extracts news headlines",
        "Develop a machine learning model to predict stock prices"
    ]
    
    for i, idea in enumerate(test_ideas, 1):
        print(f"\n📝 Test {i}: {idea}")
        print("-" * 40)
        
        try:
            # Process the idea
            result = await workflow.process_idea(idea, f"demo-{i}")
            
            # Display results
            print(f"✅ Status: {result.get('status', 'Unknown')}")
            print(f"📊 Complexity: {result.get('complexity', 'Unknown')}")
            print(f"⏱️  Iterations: {result.get('final_output', {}).get('iteration_count', 1)}")
            print(f"📄 Artifacts: {len(result.get('artifacts', []))} files")
            print(f"🧪 Tests Passed: {result.get('test_results', {}).get('passed', False)}")
            
            if result.get('artifacts'):
                print("\n📁 Generated Files:")
                for artifact in result['artifacts']:
                    print(f"   • {artifact['name']}")
            
        except Exception as e:
            print(f"❌ Error processing idea: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed successfully!")
    print("\n🚀 The Research Swarm System is ready for use!")
    print("   - API Server: uvicorn api.main:app --host 0.0.0.0 --port 8000")
    print("   - Worker: python -m orchestrator.worker")
    print("   - Docker: docker-compose up")

if __name__ == "__main__":
    asyncio.run(demo())