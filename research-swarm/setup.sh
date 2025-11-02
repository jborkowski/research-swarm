#!/bin/bash
# Setup script for Research Swarm with uv virtual environment

set -e  # Exit on any error

echo "Research Swarm Setup Script"
echo "============================"

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -ne 1 ]]; then
    echo "Error: Python 3.11 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Check if uv is installed, install if not
if ! command -v uv &> /dev/null; then
    echo "Installing uv (fast Python package installer)..."
    if command -v curl &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    elif command -v pip &> /dev/null; then
        echo "Installing uv via pip..."
        pip install uv
    else
        echo "Error: Neither curl nor pip is available to install uv"
        echo "Please install uv manually: https://github.com/astral-sh/uv"
        exit 1
    fi
fi

echo "Creating virtual environment with uv..."
uv venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
uv pip install -r pyproject.toml

echo "Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the API server:"
echo "  uvicorn api.main:app --reload"
echo ""
echo "To run the worker:"
echo "  python orchestrator/worker.py"