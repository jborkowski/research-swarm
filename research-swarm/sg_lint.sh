#!/bin/bash
# Lint script for Research Swarm project
# Run ast-grep linting on the codebase

echo "Running ast-grep linting on Research Swarm project..."
echo

# Run scan with our custom rules
sg scan

echo
echo "Linting complete!"
echo "To run specific checks, you can use commands like:"
echo "  sg run --pattern 'except:' --lang Python"
echo "  sg run --pattern 'import $MOD' --lang Python"