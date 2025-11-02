# Virtual Environment Setup for Research Swarm

# Using uv (recommended - faster and more reliable)
# Install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv           # Create virtual environment
source .venv/bin/activate  # Activate environment
uv pip install -r pyproject.toml  # Install dependencies from pyproject.toml

# Alternative: Using venv (built-in Python module)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r pyproject.toml

# Usage:
# Always activate the virtual environment before running the application:
source .venv/bin/activate  # or source venv/bin/activate

# To run the API:
uvicorn api.main:app --reload

# To run the worker:
python orchestrator/worker.py

# For development with additional tools:
uv pip install -r pyproject.toml && uv pip install ast-grep