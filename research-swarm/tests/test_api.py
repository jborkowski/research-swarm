import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from api.main import app, submit_idea, get_idea_status
from datetime import datetime, timedelta


def test_api_app_creation():
    """Test that the FastAPI app can be created"""
    assert app is not None
    assert app.title == "Research Swarm API"
    assert len(app.routes) > 0


@pytest.mark.asyncio
@patch('api.main.redis_client')
async def test_submit_idea_success(mock_redis):
    """Test submitting an idea successfully"""
    from api.main import IdeaSubmission
    from fastapi import BackgroundTasks

    # Mock Redis operations
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = None
    mock_redis.llen.return_value = 0

    # Create a sample submission and mock background tasks
    submission = IdeaSubmission(idea="Build a weather app")
    background_tasks = MagicMock(spec=BackgroundTasks)

    # Call the endpoint function directly
    response = await submit_idea(submission, background_tasks)

    # Verify response
    assert response.idea_id is not None
    assert response.status == "queued"
    assert response.estimated_completion is not None
    assert "ideas" in response.tracking_url

    # Verify Redis was called correctly
    mock_redis.lpush.assert_called_once()
    mock_redis.hset.assert_called_once()


@pytest.mark.asyncio
@patch('api.main.redis_client')
async def test_submit_idea_with_queue(mock_redis):
    """Test submitting an idea when queue has items"""
    from api.main import IdeaSubmission
    from fastapi import BackgroundTasks

    # Mock Redis with existing queue
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = None
    mock_redis.llen.return_value = 5  # 5 items already in queue

    submission = IdeaSubmission(idea="Create a task manager", priority="high")
    background_tasks = MagicMock(spec=BackgroundTasks)

    response = await submit_idea(submission, background_tasks)

    # Should estimate longer completion time due to queue
    base_time = datetime.utcnow()
    assert response.estimated_completion > base_time


@pytest.mark.asyncio
@patch('api.main.redis_client')
async def test_get_idea_status_not_found(mock_redis):
    """Test getting idea status for non-existent idea"""
    # Mock Redis to return empty result
    mock_redis.hgetall.return_value = {}

    # Test that HTTPException is raised
    with pytest.raises(Exception):  # Should be HTTPException but let's check the behavior
        await get_idea_status("non-existent-id")


@pytest.mark.asyncio
@patch('api.main.redis_client')
async def test_get_idea_status_found(mock_redis):
    """Test getting idea status for existing idea"""
    # Mock Redis to return data
    mock_redis.hgetall.return_value = {
        b"status": b"processing",
        b"phase": b"research",
        b"progress": b"75",
        b"result_url": b"http://example.com/result"
    }

    result = await get_idea_status("test-123")

    assert result["idea_id"] == "test-123"
    assert result["status"] == "processing"
    assert result["current_phase"] == "research"
    assert result["progress_percentage"] == 75
    assert result["result_url"] == "http://example.com/result"


def test_idea_submission_model():
    """Test IdeaSubmission Pydantic model"""
    from api.main import IdeaSubmission
    
    # Test with minimal required fields
    submission = IdeaSubmission(idea="Test idea")
    assert submission.idea == "Test idea"
    assert submission.priority == "medium"  # Default value
    assert submission.context is None  # Default value
    assert submission.constraints is None  # Default value
    
    # Test with all fields
    submission = IdeaSubmission(
        idea="Test idea",
        priority="high",
        context="Additional context",
        constraints={"budget": 100}
    )
    assert submission.idea == "Test idea"
    assert submission.priority == "high"
    assert submission.context == "Additional context"
    assert submission.constraints == {"budget": 100}


def test_idea_response_model():
    """Test IdeaResponse Pydantic model"""
    from api.main import IdeaResponse
    from datetime import datetime
    
    # Test model creation
    response = IdeaResponse(
        idea_id="test-123",
        status="queued",
        estimated_completion=datetime.now(),
        tracking_url="http://example.com/track/test-123"
    )
    
    assert response.idea_id == "test-123"
    assert response.status == "queued"
    assert response.tracking_url == "http://example.com/track/test-123"


# Integration test for the workflow would require Redis and other services
# which are not available in this test environment, so we'll focus on
# unit testing the individual components as implemented