#!/usr/bin/env python3
"""
Initialize the research output repository
"""
import os
import git
from pathlib import Path

def initialize_repository(repo_path: str):
    """Initialize the output git repository"""
    repo_path = Path(repo_path)
    
    # Create the repository directory if it doesn't exist
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize git repository if it doesn't exist
    if not (repo_path / '.git').exists():
        repo = git.Repo.init(repo_path)
        
        # Create initial files
        readme_path = repo_path / 'README.md'
        if not readme_path.exists():
            readme_path.write_text('# Research Swarm Output Repository\n\nThis repository contains research and implementation outputs from the Research Swarm system.\n')
        
        # Add and commit initial files
        repo.index.add([str(readme_path)])
        repo.index.commit('Initialize research repository')
        
        print(f"Initialized research repository at {repo_path}")
    else:
        print(f"Repository already exists at {repo_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = "/home/user/research-output"  # Default path from settings
    
    initialize_repository(repo_path)