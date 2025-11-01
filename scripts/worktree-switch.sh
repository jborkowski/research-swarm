#!/usr/bin/env bash
# Helper functions for switching between worktrees
# Source this file in your shell: source scripts/worktree-switch.sh

wt() {
    local identifier="$1"

    if [ -z "$identifier" ]; then
        echo "Available worktrees:"
        git worktree list
        return 0
    fi

    local repo_name=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)")
    local worktree_path=""

    # Check if it's a full path
    if [ -d "$identifier" ]; then
        worktree_path="$identifier"
    else
        # Try to find by branch name in worktree list
        worktree_path=$(git worktree list --porcelain | awk -v branch="$identifier" '
            /^worktree / { path = substr($0, 10) }
            /^branch / {
                if ($0 ~ branch) {
                    print path
                    exit
                }
            }
        ')

        # If not found, try the default naming pattern
        if [ -z "$worktree_path" ] || [ ! -d "$worktree_path" ]; then
            worktree_path="../${repo_name}-${identifier}"
        fi
    fi

    if [ ! -d "$worktree_path" ]; then
        echo "Error: Worktree not found for: $identifier"
        echo "Available worktrees:"
        git worktree list
        return 1
    fi

    cd "$worktree_path" || return 1
    echo "Switched to worktree: $worktree_path"
    git status --short --branch
}

# Bash completion for wt command
_wt_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local branches=$(git worktree list --porcelain | awk '/^branch / {
        branch = substr($0, 8)
        gsub("refs/heads/", "", branch)
        print branch
    }')
    COMPREPLY=($(compgen -W "$branches" -- "$cur"))
}

complete -F _wt_complete wt

echo "Worktree switch function loaded!"
echo "Usage: wt [branch-name]"
echo "  wt              - List all worktrees"
echo "  wt main         - Switch to main branch worktree"
echo "  wt feature-xyz  - Switch to feature-xyz worktree"
