import pytest
import tempfile
from pathlib import Path
from utils.repository import RepositoryManager


@pytest.fixture
def temp_repo():
    """Create temporary repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_repository_initialization(temp_repo):
    """Test repository initialization."""
    repo_manager = RepositoryManager(temp_repo)

    assert Path(temp_repo).exists()
    assert (Path(temp_repo) / ".git").exists()
    assert (Path(temp_repo) / "README.md").exists()


def test_create_idea_folder(temp_repo):
    """Test creating idea folder."""
    repo_manager = RepositoryManager(temp_repo)

    idea_path = repo_manager.create_idea_folder(
        "test-id",
        "Test idea for repository"
    )

    assert idea_path.exists()
    assert (idea_path / "metadata.json").exists()
    assert (idea_path / "research").exists()
    assert (idea_path / "plan").exists()
    assert (idea_path / "implementation").exists()
    assert (idea_path / "results").exists()


def test_sanitize_name(temp_repo):
    """Test name sanitization."""
    repo_manager = RepositoryManager(temp_repo)

    safe_name = repo_manager._sanitize_name("Test Idea with Special Characters!@#")

    assert safe_name == "test-idea-with-special-characters"
    assert len(safe_name) <= 50


def test_save_research(temp_repo):
    """Test saving research results."""
    repo_manager = RepositoryManager(temp_repo)

    idea_path = repo_manager.create_idea_folder("test-id", "Test idea")

    research_data = {
        "synthesis": {
            "feasible": True,
            "confidence": 0.8,
            "recommendations": ["Use FastAPI"],
            "blockers": []
        },
        "results": []
    }

    repo_manager.save_research(idea_path, research_data)

    assert (idea_path / "research" / "README.md").exists()
    assert (idea_path / "research" / "research_data.json").exists()
    assert (idea_path / "research" / "feasibility.md").exists()
