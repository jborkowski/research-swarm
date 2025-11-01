import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('api.main.redis_client') as mock:
        mock.ping.return_value = True
        mock.lpush.return_value = 1
        mock.llen.return_value = 1
        mock.hset.return_value = 1
        mock.hgetall.return_value = {
            "status": "queued",
            "phase": "pending",
            "progress": "0",
            "logs": "[]"
        }
        yield mock


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Research Swarm API"
    assert data["status"] == "healthy"


def test_health_check_healthy(client, mock_redis):
    """Test health check when Redis is healthy."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["redis"] == "connected"


def test_submit_idea(client, mock_redis):
    """Test submitting a new idea."""
    response = client.post(
        "/api/v1/ideas",
        json={
            "idea": "Create a test application",
            "priority": "medium"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "idea_id" in data
    assert data["status"] == "queued"
    assert "tracking_url" in data


def test_get_idea_status(client, mock_redis):
    """Test getting idea status."""
    response = client.get("/api/v1/ideas/test-id/status")

    assert response.status_code == 200
    data = response.json()
    assert data["idea_id"] == "test-id"
    assert "status" in data


def test_get_queue_stats(client, mock_redis):
    """Test getting queue statistics."""
    response = client.get("/api/v1/queue/stats")

    assert response.status_code == 200
    data = response.json()
    assert "queue_length" in data
    assert "estimated_wait_minutes" in data
