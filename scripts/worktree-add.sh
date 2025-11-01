#!/usr/bin/env bash
# Create a new git worktree

set -e

usage() {
    echo "Usage: $0 <branch-name> [path]"
    echo ""
    echo "Creates a new worktree for the specified branch."
    echo "If path is not provided, it will be created as ../research-swarm-<branch-name>"
    echo ""
    echo "Examples:"
    echo "  $0 feature-xyz              # Creates ../research-swarm-feature-xyz"
    echo "  $0 feature-xyz /tmp/wt      # Creates /tmp/wt"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

BRANCH="$1"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

if [ -n "$2" ]; then
    PATH_NAME="$2"
else
    PATH_NAME="../${REPO_NAME}-${BRANCH}"
fi

echo "Creating worktree for branch: $BRANCH"
echo "Path: $PATH_NAME"
echo ""

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "Branch '$BRANCH' exists, checking out..."
    git worktree add "$PATH_NAME" "$BRANCH"
else
    echo "Branch '$BRANCH' doesn't exist, creating new branch..."
    git worktree add -b "$BRANCH" "$PATH_NAME"
fi

echo ""
echo "Worktree created successfully!"
echo "Switch to it with: wt $BRANCH"
