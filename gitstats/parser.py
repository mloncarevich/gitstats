"""Git log parsing utilities."""

import subprocess
from datetime import datetime
from pathlib import Path


def get_commit_stats(repo_path: str = ".") -> dict | None:
    """
    Parse git log and return commit statistics.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Dictionary with commit statistics or None if not a git repo
    """
    path = Path(repo_path).resolve()
    
    if not (path / ".git").exists():
        return None
    
    try:
        # Get all commits with author and date
        result = subprocess.run(
            ["git", "log", "--format=%H|%an|%ae|%aI"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    
    lines = result.stdout.strip().split("\n")
    
    if not lines or lines[0] == "":
        return None
    
    commits = []
    authors = set()
    
    for line in lines:
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 4:
            commit_hash, author_name, author_email, date_str = parts[:4]
            authors.add(author_name)
            commits.append({
                "hash": commit_hash,
                "author": author_name,
                "email": author_email,
                "date": datetime.fromisoformat(date_str),
            })
    
    if not commits:
        return None
    
    # Sort by date
    commits.sort(key=lambda x: x["date"])
    
    return {
        "total_commits": len(commits),
        "total_authors": len(authors),
        "first_commit": commits[0]["date"].strftime("%Y-%m-%d"),
        "last_commit": commits[-1]["date"].strftime("%Y-%m-%d"),
        "commits": commits,
        "authors": list(authors),
    }
