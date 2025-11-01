import asyncio
import json
import logging
from redis import Redis
from datetime import datetime

from orchestrator.workflow import ResearchWorkflow
from utils.repository import RepositoryManager
from config.settings import settings

logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Worker:
    """Background worker that processes ideas from the queue."""

    def __init__(self):
        self.redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        self.repo_manager = RepositoryManager(settings.repository_path)
        self.workflow = ResearchWorkflow(self.repo_manager)
        self.running = False

    async def start(self):
        """Start the worker."""
        self.running = True
        logger.info("Worker started - waiting for ideas...")

        while self.running:
            try:
                job_data = self.redis_client.brpop("idea_queue", timeout=5)

                if job_data:
                    _, job_json = job_data
                    job = json.loads(job_json)

                    logger.info(f"Processing job: {job['idea_id']}")

                    await self.process_job(job)

                await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)

    async def process_job(self, job: dict):
        """Process a single job."""
        idea_id = job["idea_id"]

        try:
            self._update_status(idea_id, "processing", "planning", 10)

            result = await self.workflow.process_idea(
                idea_text=job["idea"],
                idea_id=idea_id,
                context=job.get("context")
            )

            status = "completed" if result.get("status") != "failed" else "failed"

            self._update_status(
                idea_id,
                status,
                "completed",
                100,
                result_url=self._get_result_url(idea_id)
            )

            logger.info(f"Job {idea_id} completed with status: {status}")

        except Exception as e:
            logger.error(f"Job {idea_id} failed: {e}")

            self._update_status(
                idea_id,
                "failed",
                "error",
                0,
                error=str(e)
            )

    def _update_status(
        self,
        idea_id: str,
        status: str,
        phase: str,
        progress: int,
        result_url: str = None,
        error: str = None
    ):
        """Update job status in Redis."""
        try:
            updates = {
                "status": status,
                "phase": phase,
                "progress": str(progress),
                "updated_at": datetime.utcnow().isoformat()
            }

            if result_url:
                updates["result_url"] = result_url

            if error:
                logs = self.redis_client.hget(f"idea:{idea_id}", "logs")
                logs_list = json.loads(logs) if logs else []
                logs_list.append(f"ERROR: {error}")
                updates["logs"] = json.dumps(logs_list)

            self.redis_client.hset(f"idea:{idea_id}", mapping=updates)

        except Exception as e:
            logger.error(f"Failed to update status for {idea_id}: {e}")

    def _get_result_url(self, idea_id: str) -> str:
        """Get the result URL for an idea."""
        idea_path = self.workflow._get_idea_path(idea_id)
        if idea_path:
            return f"file://{idea_path}/SUMMARY.md"
        return None

    def stop(self):
        """Stop the worker gracefully."""
        logger.info("Stopping worker...")
        self.running = False


async def main():
    """Main entry point."""
    worker = Worker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
