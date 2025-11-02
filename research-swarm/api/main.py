from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timedelta
from redis import Redis
import json
import psutil
import os

from config.settings import settings
from utils.metrics import MetricsCollector
from prometheus_client import generate_latest

app = FastAPI(title="Research Swarm API")
redis_client = Redis.from_url(settings.redis_url)

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

@app.post("/api/v1/ideas", response_model=IdeaResponse)
async def submit_idea(
    submission: IdeaSubmission,
    background_tasks: BackgroundTasks
):
    # Generate unique ID
    idea_id = str(uuid.uuid4())
    
    # Create job payload
    job_data = {
        "idea_id": idea_id,
        "idea": submission.idea,
        "priority": submission.priority,
        "context": submission.context,
        "constraints": submission.constraints,
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "queued"
    }
    
    # Queue for processing
    redis_client.lpush("idea_queue", json.dumps(job_data))
    
    # Store metadata (filter out None values for Redis compatibility)
    filtered_job_data = {k: v for k, v in job_data.items() if v is not None}
    redis_client.hset(f"idea:{idea_id}", mapping=filtered_job_data)
    
    # Calculate estimated completion
    queue_length = redis_client.llen("idea_queue")
    estimated_minutes = queue_length * 30  # 30 min average per idea
    estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_minutes)
    
    return IdeaResponse(
        idea_id=idea_id,
        status="queued",
        estimated_completion=estimated_completion,
        tracking_url=f"https://localhost:8000/ideas/{idea_id}"
    )

@app.get("/api/v1/ideas/{idea_id}/status")
async def get_idea_status(idea_id: str):
    data = redis_client.hgetall(f"idea:{idea_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "idea_id": idea_id,
        "status": data.get(b"status", b"unknown").decode(),
        "current_phase": data.get(b"phase", b"").decode(),
        "progress_percentage": int(data.get(b"progress", 0)),
        "result_url": data.get(b"result_url", b"").decode() or None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check Redis connectivity
        redis_client.ping()

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Update metrics
        MetricsCollector.update_active_pods(1)  # This would be dynamic in K8s

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "redis": "connected",
                "api": "running"
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)