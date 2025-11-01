from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timedelta
from redis import Redis
import json
import logging

from config.settings import settings

app = FastAPI(
    title="Research Swarm API",
    description="AI-powered research automation system",
    version="1.0.0"
)

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

try:
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


class IdeaSubmission(BaseModel):
    idea: str
    priority: str = "medium"
    context: Optional[str] = None
    constraints: Optional[dict] = None


class IdeaResponse(BaseModel):
    idea_id: str
    status: str
    estimated_completion: datetime
    tracking_url: str


class StatusResponse(BaseModel):
    idea_id: str
    status: str
    current_phase: Optional[str]
    progress_percentage: int
    logs: list[str]
    result_url: Optional[str]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Research Swarm API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    redis_healthy = False
    if redis_client:
        try:
            redis_client.ping()
            redis_healthy = True
        except:
            pass

    return {
        "status": "healthy" if redis_healthy else "degraded",
        "redis": "connected" if redis_healthy else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/ideas", response_model=IdeaResponse)
async def submit_idea(
    submission: IdeaSubmission,
    background_tasks: BackgroundTasks
):
    """Submit a new idea for research and implementation."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Queue service unavailable")

    idea_id = str(uuid.uuid4())

    job_data = {
        "idea_id": idea_id,
        "idea": submission.idea,
        "priority": submission.priority,
        "context": submission.context,
        "constraints": submission.constraints or {},
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "queued",
        "phase": "pending",
        "progress": 0,
        "logs": []
    }

    try:
        redis_client.lpush("idea_queue", json.dumps(job_data))
        redis_client.hset(f"idea:{idea_id}", mapping={
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in job_data.items()
        })

        queue_length = redis_client.llen("idea_queue")
        estimated_minutes = queue_length * 30
        estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_minutes)

        logger.info(f"Idea {idea_id} queued successfully")

        return IdeaResponse(
            idea_id=idea_id,
            status="queued",
            estimated_completion=estimated_completion,
            tracking_url=f"http://{settings.api_host}:{settings.api_port}/ideas/{idea_id}"
        )
    except Exception as e:
        logger.error(f"Failed to queue idea: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ideas/{idea_id}/status", response_model=StatusResponse)
async def get_idea_status(idea_id: str):
    """Get the status of a submitted idea."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Queue service unavailable")

    try:
        data = redis_client.hgetall(f"idea:{idea_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Idea not found")

        logs_data = data.get("logs", "[]")
        logs = json.loads(logs_data) if isinstance(logs_data, str) else logs_data

        return StatusResponse(
            idea_id=idea_id,
            status=data.get("status", "unknown"),
            current_phase=data.get("phase", None),
            progress_percentage=int(data.get("progress", 0)),
            logs=logs,
            result_url=data.get("result_url", None)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/ideas/{idea_id}")
async def cancel_idea(idea_id: str):
    """Cancel a queued or processing idea."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Queue service unavailable")

    try:
        data = redis_client.hgetall(f"idea:{idea_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Idea not found")

        if data.get("status") in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel idea with status: {data.get('status')}"
            )

        redis_client.hset(f"idea:{idea_id}", "status", "cancelled")

        logger.info(f"Idea {idea_id} cancelled")

        return {"idea_id": idea_id, "status": "cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/queue/stats")
async def get_queue_stats():
    """Get queue statistics."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Queue service unavailable")

    try:
        queue_length = redis_client.llen("idea_queue")
        return {
            "queue_length": queue_length,
            "estimated_wait_minutes": queue_length * 30
        }
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
