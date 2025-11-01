#!/usr/bin/env bash
# Remove a git worktree

set -e

usage() {
    echo "Usage: $0 <path-or-branch>"
    echo ""
    echo "Removes the specified worktree."
    echo "You can specify either the full path or just the branch name."
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

IDENTIFIER="$1"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

# Check if it's a full path
if [ -d "$IDENTIFIER" ]; then
    WORKTREE_PATH="$IDENTIFIER"
else
    # Try to find by branch name
    WORKTREE_PATH=$(git worktree list --porcelain | awk -v branch="$IDENTIFIER" '
        /^worktree / { path = substr($0, 10) }
        /^branch / {
            if ($0 ~ branch) {
                print path
                exit
            }
        }
    ')

    # If not found, try the default naming pattern
    if [ -z "$WORKTREE_PATH" ]; then
        WORKTREE_PATH="../${REPO_NAME}-${IDENTIFIER}"
    fi
fi

if [ ! -d "$WORKTREE_PATH" ]; then
    echo "Error: Worktree not found: $WORKTREE_PATH"
    exit 1
fi

echo "Removing worktree: $WORKTREE_PATH"
read -p "Are you sure? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

git worktree remove "$WORKTREE_PATH"
echo "Worktree removed successfully!"
