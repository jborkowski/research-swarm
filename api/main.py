from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timedelta
from redis import Redis
import json

# Import settings
try:
    from config.settings import settings
    redis_client = Redis.from_url(settings.redis_url)
except Exception as e:
    print(f"Warning: Could not load settings, using default Redis connection: {e}")
    redis_client = Redis.from_url("redis://localhost:6379")

app = FastAPI(title="Research Swarm API")

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
    
    # Store metadata
    redis_client.hset(f"idea:{idea_id}", mapping=job_data)
    
    # Calculate estimated completion
    queue_length = redis_client.llen("idea_queue")
    estimated_minutes = queue_length * 30  # 30 min average per idea
    estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_minutes)
    
    return IdeaResponse(
        idea_id=idea_id,
        status="queued",
        estimated_completion=estimated_completion,
        tracking_url=f"http://localhost:8000/api/v1/ideas/{idea_id}"
    )

@app.get("/api/v1/ideas/{idea_id}/status")
async def get_idea_status(idea_id: str):
    data = redis_client.hgetall(f"idea:{idea_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    # Decode bytes to strings
    decoded_data = {}
    for key, value in data.items():
        decoded_data[key.decode() if isinstance(key, bytes) else key] = value.decode() if isinstance(value, bytes) else value
    
    return {
        "idea_id": idea_id,
        "status": decoded_data.get("status", "unknown"),
        "current_phase": decoded_data.get("phase", ""),
        "progress_percentage": int(decoded_data.get("progress", 0)),
        "result_url": decoded_data.get("result_url", None) or None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)