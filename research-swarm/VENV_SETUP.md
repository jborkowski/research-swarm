# Virtual Environment Setup for Research Swarm

# Option 1: Using venv (built-in Python module)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Option 2: Using uv (faster pip replacement)
# Install uv first: pip install uv or curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv           # Create virtual environment
source .venv/bin/activate  # Activate environment
uv pip install -r requirements.txt  # Install dependencies

# Usage:
# Always activate the virtual environment before running the application:
source venv/bin/activate  # or source .venv/bin/activate if using uv

# To run the API:
# uvicorn api.main:app --reload

# To run the worker:
# python orchestrator/worker.py