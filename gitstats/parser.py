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
            commits.append(
                {
                    "hash": commit_hash,
                    "author": author_name,
                    "email": author_email,
                    "date": datetime.fromisoformat(date_str),
                }
            )

    if not commits:
        return None

    # Sort by date
    commits.sort(key=lambda x: x["date"])

    # Calculate author statistics
    author_stats = get_author_stats(commits)

    return {
        "total_commits": len(commits),
        "total_authors": len(authors),
        "first_commit": commits[0]["date"].strftime("%Y-%m-%d"),
        "last_commit": commits[-1]["date"].strftime("%Y-%m-%d"),
        "commits": commits,
        "authors": list(authors),
        "author_stats": author_stats,
    }


def get_author_stats(commits: list[dict]) -> list[dict]:
    """
    Calculate commit statistics per author.

    Args:
        commits: List of commit dictionaries

    Returns:
        List of author statistics sorted by commit count (descending)
    """
    from collections import Counter

    author_counts = Counter(commit["author"] for commit in commits)
    total = len(commits)

    stats = []
    for author, count in author_counts.most_common():
        percentage = (count / total) * 100
        stats.append(
            {
                "author": author,
                "commits": count,
                "percentage": percentage,
            }
        )

    return stats


def get_activity_heatmap(commits: list[dict]) -> dict:
    """
    Calculate commit activity by day of week and hour.

    Args:
        commits: List of commit dictionaries

    Returns:
        Dictionary with heatmap data (day -> hour -> count)
    """
    from collections import defaultdict

    # Initialize heatmap: 7 days x 24 hours
    heatmap = defaultdict(lambda: defaultdict(int))

    for commit in commits:
        date = commit["date"]
        day = date.weekday()  # 0=Monday, 6=Sunday
        hour = date.hour
        heatmap[day][hour] += 1

    # Find max for normalization
    max_count = (
        max(count for day_data in heatmap.values() for count in day_data.values()) if heatmap else 1
    )

    return {
        "data": dict(heatmap),
        "max_count": max_count,
    }


def get_weekly_activity(commits: list[dict]) -> list[dict]:
    """
    Calculate commit activity by day of week.

    Args:
        commits: List of commit dictionaries

    Returns:
        List of day statistics
    """
    from collections import Counter

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_counts = Counter(commit["date"].weekday() for commit in commits)
    total = len(commits)

    return [
        {
            "day": days[i],
            "commits": day_counts.get(i, 0),
            "percentage": (day_counts.get(i, 0) / total * 100) if total else 0,
        }
        for i in range(7)
    ]


def get_hourly_activity(commits: list[dict]) -> list[dict]:
    """
    Calculate commit activity by hour of day.

    Args:
        commits: List of commit dictionaries

    Returns:
        List of hourly statistics
    """
    from collections import Counter

    hour_counts = Counter(commit["date"].hour for commit in commits)
    total = len(commits)

    return [
        {
            "hour": h,
            "commits": hour_counts.get(h, 0),
            "percentage": (hour_counts.get(h, 0) / total * 100) if total else 0,
        }
        for h in range(24)
    ]


def get_commit_streaks(commits: list[dict]) -> dict:
    """
    Calculate commit streaks (consecutive days with commits).

    Args:
        commits: List of commit dictionaries

    Returns:
        Dictionary with streak statistics
    """
    from datetime import timedelta

    if not commits:
        return {"current_streak": 0, "longest_streak": 0, "total_active_days": 0}

    # Get unique dates (just the date part, no time)
    commit_dates = sorted({commit["date"].date() for commit in commits})

    if not commit_dates:
        return {"current_streak": 0, "longest_streak": 0, "total_active_days": 0}

    # Calculate streaks
    streaks = []
    current_streak = 1

    for i in range(1, len(commit_dates)):
        if commit_dates[i] - commit_dates[i - 1] == timedelta(days=1):
            current_streak += 1
        else:
            streaks.append(current_streak)
            current_streak = 1

    streaks.append(current_streak)

    longest_streak = max(streaks) if streaks else 0

    # Check if current streak is active (last commit was today or yesterday)
    from datetime import date

    today = date.today()
    last_commit_date = commit_dates[-1]
    days_since_last = (today - last_commit_date).days

    if days_since_last <= 1:
        active_streak = streaks[-1] if streaks else 0
    else:
        active_streak = 0

    return {
        "current_streak": active_streak,
        "longest_streak": longest_streak,
        "total_active_days": len(commit_dates),
        "last_commit_date": str(last_commit_date),
    }
