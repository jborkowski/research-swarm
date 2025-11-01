import asyncio
import json
import time
from redis import Redis
from datetime import datetime

# Import local modules
from orchestrator.workflow import ResearchWorkflow
from utils.repository import RepositoryManager
from config.settings import settings

class ResearchWorker:
    def __init__(self):
        self.redis_client = Redis.from_url(settings.redis_url if settings else "redis://localhost:6379")
        self.workflow = ResearchWorkflow()
        self.repo_manager = RepositoryManager(settings.repository_path if settings else "./research-output")
        
    async def start_worker(self):
        """Start the research worker to process ideas from the queue"""
        print("Research Worker started. Waiting for ideas...")
        
        while True:
            try:
                # Get idea from queue
                idea_data = self.redis_client.brpop("idea_queue", timeout=5)
                
                if idea_data:
                    # Process the idea
                    await self.process_idea(idea_data[1])
                else:
                    # No ideas in queue, wait a bit
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"Error processing idea: {e}")
                await asyncio.sleep(5)
    
    async def process_idea(self, idea_json: bytes):
        """Process a single idea through the research workflow"""
        try:
            # Parse idea data
            idea_data = json.loads(idea_json.decode())
            idea_id = idea_data["idea_id"]
            idea_text = idea_data["idea"]
            
            print(f"Processing idea {idea_id}: {idea_text}")
            
            # Update status in Redis
            self._update_idea_status(idea_id, "processing", "planning", 10)
            
            # Create idea folder in repository
            idea_path = self.repo_manager.create_idea_folder(idea_id, idea_text)
            
            # Process through workflow
            result = await self.workflow.process_idea(idea_text, idea_id)
            
            # Save results to repository
            await self._save_results(idea_path, result)
            
            # Update final status
            self._update_idea_status(idea_id, "completed", "finished", 100)
            
            print(f"Completed processing idea {idea_id}")
            
        except Exception as e:
            print(f"Error processing idea {idea_id}: {e}")
            self._update_idea_status(idea_id, "failed", "error", 0)
    
    def _update_idea_status(self, idea_id: str, status: str, phase: str = "", progress: int = 0):
        """Update idea status in Redis"""
        try:
            self.redis_client.hset(f"idea:{idea_id}", mapping={
                "status": status,
                "phase": phase,
                "progress": progress,
                "updated_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f"Warning: Could not update status for {idea_id}: {e}")
    
    async def _save_results(self, idea_path, result):
        """Save research results to the repository"""
        try:
            # Save implementation artifacts
            if "artifacts" in result:
                self.repo_manager.save_implementation(idea_path, result["artifacts"])
            
            # Save test results
            if "test_results" in result:
                self.repo_manager.save_test_results(idea_path, result["test_results"])
            
            # Finalize with summary
            self.repo_manager.finalize_idea(idea_path, result)
            
        except Exception as e:
            print(f"Warning: Could not save results to repository: {e}")

async def main():
    """Main entry point for the worker"""
    worker = ResearchWorker()
    await worker.start_worker()

if __name__ == "__main__":
    asyncio.run(main())