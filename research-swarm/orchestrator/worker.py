#!/usr/bin/env python3
"""
Research Swarm Worker
Processes ideas from the queue and executes the research workflow
"""
import asyncio
import json
from datetime import datetime
from redis import Redis

from config.settings import settings
from orchestrator.workflow import ResearchWorkflow
from utils.repository import RepositoryManager
from utils.logging import logger
from utils.metrics import MetricsCollector

redis_client = Redis.from_url(settings.redis_url)

async def process_idea_from_queue():
    """Process a single idea from the queue"""
    # Get idea from queue
    queue_item = redis_client.brpop("idea_queue", timeout=5)
    if not queue_item:
        return  # No items in queue
    
    _, idea_json = queue_item
    idea_data = json.loads(idea_json)
    
    idea_id = idea_data["idea_id"]
    idea_text = idea_data["idea"]
    
    logger.info(f"Processing idea {idea_id}: {idea_text[:50]}...")
    
    # Update status in Redis
    redis_client.hset(f"idea:{idea_id}", mapping={
        "status": "processing",
        "phase": "initial"
    })
    
    start_time = datetime.now()
    
    try:
        # Initialize repository manager
        repo_manager = RepositoryManager(settings.repository_path)
        
        # Create idea folder
        idea_path = repo_manager.create_idea_folder(idea_id, idea_text)
        
        # Initialize workflow
        workflow = ResearchWorkflow()
        
        # Process the idea
        result = await workflow.process_idea(idea_text, idea_id)
        
        # Save implementation if available
        if result and "implementation" in result:
            repo_manager.save_implementation(idea_path, result["implementation"])
        
        # Save test results if available
        if result and "test_results" in result:
            repo_manager.save_test_results(idea_path, result["test_results"])
        
        # Finalize the idea
        repo_manager.finalize_idea(idea_path, result or {"summary": "Processing completed"})
        
        # Update status
        redis_client.hset(f"idea:{idea_id}", mapping={
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        })
        
        # Record metrics
        duration = (datetime.now() - start_time).total_seconds()
        MetricsCollector.record_idea_processed(success=True, duration=duration)
        
        logger.info(f"Completed idea {idea_id} in {duration}s")
        
    except Exception as e:
        logger.error(f"Error processing idea {idea_id}: {str(e)}")
        
        # Update status to failed
        redis_client.hset(f"idea:{idea_id}", mapping={
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })
        
        # Record metrics
        duration = (datetime.now() - start_time).total_seconds()
        MetricsCollector.record_idea_processed(success=False, duration=duration)

async def main():
    """Main worker loop"""
    logger.info("Research Swarm Worker starting...")
    
    while True:
        try:
            await process_idea_from_queue()
        except Exception as e:
            logger.error(f"Worker error: {str(e)}")
            await asyncio.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    asyncio.run(main())