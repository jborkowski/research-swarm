import pytest
import os


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-key")
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["LOG_LEVEL"] = "ERROR"
    os.environ["REPO_PATH"] = "/tmp/test-repo"


@pytest.fixture
def sample_idea():
    """Sample idea for testing."""
    return {
        "idea_id": "test-123",
        "idea_text": "Create a simple TODO application",
        "context": "Use modern web technologies"
    }


@pytest.fixture
def sample_plan():
    """Sample implementation plan."""
    return {
        "complexity": "simple",
        "needs_research": False,
        "feasible": True,
        "requirements": {
            "type": "web_app",
            "key_features": ["Add tasks", "Mark complete"],
            "constraints": []
        },
        "dependencies": ["fastapi", "react"],
        "estimated_effort_minutes": 30
    }
