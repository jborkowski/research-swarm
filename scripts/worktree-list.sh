#!/usr/bin/env bash
# List all git worktrees with enhanced formatting

set -e

echo "Git Worktrees:"
echo "=============="
git worktree list --porcelain | awk '
BEGIN { count = 0 }
/^worktree / {
    if (count > 0) print ""
    count++
    path = substr($0, 10)
    printf "  %d. %s\n", count, path
}
/^HEAD / { printf "     HEAD: %s\n", substr($0, 6) }
/^branch / {
    branch = substr($0, 8)
    gsub("refs/heads/", "", branch)
    printf "     Branch: %s\n", branch
}
/^bare/ { printf "     (bare repository)\n" }
'

echo ""
echo "Total worktrees: $(git worktree list | wc -l | tr -d ' ')"
