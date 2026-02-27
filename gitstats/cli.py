"""Command-line interface for gitstats."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from gitstats import __version__

app = typer.Typer(
    name="gitstats",
    help="Beautiful git statistics in your terminal 📊",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]gitstats[/] version [green]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """gitstats - Beautiful git statistics in your terminal."""
    pass


@app.command()
def stats(
    path: str = typer.Argument(".", help="Path to git repository"),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output statistics as JSON",
    ),
    since: str = typer.Option(
        None,
        "--since",
        "-s",
        help="Show commits after this date (YYYY-MM-DD)",
    ),
    until: str = typer.Option(
        None,
        "--until",
        "-u",
        help="Show commits before this date (YYYY-MM-DD)",
    ),
    author: str = typer.Option(
        None,
        "--author",
        "-a",
        help="Filter commits by author name (case-insensitive, partial match)",
    ),
    top: int = typer.Option(
        None,
        "--top",
        "-t",
        help="Show only top N contributors",
    ),
) -> None:
    """Show commit statistics for a git repository."""
    import json
    from datetime import datetime

    from gitstats.parser import (
        get_commit_stats,
        get_commit_streaks,
        get_hourly_activity,
        get_weekly_activity,
    )

    # Parse date filters
    since_date = None
    until_date = None

    if since:
        try:
            since_date = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]Invalid date format for --since: {since}. Use YYYY-MM-DD[/]")
            raise typer.Exit(1)

    if until:
        try:
            until_date = datetime.strptime(until, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]Invalid date format for --until: {until}. Use YYYY-MM-DD[/]")
            raise typer.Exit(1)

    stats_data = get_commit_stats(path)

    if not stats_data:
        if json_output:
            console.print(json.dumps({"error": "No commits found or not a git repository"}))
        else:
            console.print("[red]No commits found or not a git repository.[/]")
        raise typer.Exit(1)

    # Filter commits by date range and/or author
    commits = stats_data["commits"]
    filters_applied = []

    if since_date or until_date:
        commits = _filter_commits_by_date(commits, since_date, until_date)
        filters_applied.append("date")

    if author:
        commits = _filter_commits_by_author(commits, author)
        filters_applied.append("author")

    if filters_applied and not commits:
        error_msg = "No commits found matching the specified filters"
        if json_output:
            console.print(json.dumps({"error": error_msg}))
        else:
            console.print(f"[red]{error_msg}[/]")
        raise typer.Exit(1)

    # Recalculate stats if any filters were applied
    if filters_applied:
        from gitstats.parser import get_author_stats

        unique_authors = {c["author"] for c in commits}
        stats_data = {
            **stats_data,
            "commits": commits,
            "total_commits": len(commits),
            "total_authors": len(unique_authors),
            "first_commit": commits[0]["date"].strftime("%Y-%m-%d"),
            "last_commit": commits[-1]["date"].strftime("%Y-%m-%d"),
            "author_stats": get_author_stats(commits),
        }

    streaks = get_commit_streaks(stats_data["commits"])

    if json_output:
        # Build JSON output
        output = {
            "repository": path,
            "total_commits": stats_data["total_commits"],
            "total_authors": stats_data["total_authors"],
            "first_commit": stats_data["first_commit"],
            "last_commit": stats_data["last_commit"],
            "filters": {
                "since": since_date.strftime("%Y-%m-%d") if since_date else None,
                "until": until_date.strftime("%Y-%m-%d") if until_date else None,
                "author": author,
                "top": top,
            },
            "authors": stats_data["author_stats"][:top] if top else stats_data["author_stats"],
            "streaks": streaks,
            "weekly_activity": get_weekly_activity(stats_data["commits"]),
            "hourly_activity": get_hourly_activity(stats_data["commits"]),
        }
        console.print(json.dumps(output, indent=2))
        return

    # Pretty terminal output
    console.print(f"\n[bold]📊 Git Statistics for:[/] [cyan]{path}[/]")

    # Show filters if applied
    if filters_applied:
        filter_parts = []
        if since_date:
            filter_parts.append(f"from {since_date.strftime('%Y-%m-%d')}")
        if until_date:
            filter_parts.append(f"to {until_date.strftime('%Y-%m-%d')}")
        if author:
            filter_parts.append(f"author: {author}")
        console.print(f"[dim]Filtered: {' '.join(filter_parts)}[/]")

    console.print()

    console.print(f"[bold]Total commits:[/] [green]{stats_data['total_commits']}[/]")
    console.print(f"[bold]Contributors:[/] [green]{stats_data['total_authors']}[/]")
    console.print(f"[bold]First commit:[/] [yellow]{stats_data['first_commit']}[/]")
    console.print(f"[bold]Latest commit:[/] [yellow]{stats_data['last_commit']}[/]")
    console.print()

    # Show author breakdown table
    if stats_data.get("author_stats"):
        author_stats_display = stats_data["author_stats"]
        if top and top > 0:
            author_stats_display = author_stats_display[:top]
        _print_author_table(author_stats_display, top=top, total=len(stats_data["author_stats"]))

    # Show activity heatmap
    _print_activity_heatmap(stats_data["commits"])

    # Show streaks
    _print_streaks(streaks)


def _print_author_table(
    author_stats: list[dict], top: int | None = None, total: int | None = None
) -> None:
    """Print a table of author statistics."""
    title = "👥 Commits by Author"
    if top and total and top < total:
        title += f" (top {top} of {total})"
    table = Table(title=title, show_header=True, header_style="bold cyan")

    table.add_column("Author", style="white", no_wrap=True)
    table.add_column("Commits", justify="right", style="green")
    table.add_column("Percentage", justify="right", style="yellow")
    table.add_column("", justify="left", style="blue")  # Progress bar

    for stat in author_stats:
        bar_width = int(stat["percentage"] / 2)  # Max 50 chars for 100%
        bar = "█" * bar_width

        table.add_row(
            stat["author"],
            str(stat["commits"]),
            f"{stat['percentage']:.1f}%",
            bar,
        )

    console.print(table)
    console.print()


def _print_activity_heatmap(commits: list[dict]) -> None:
    """Print activity heatmap by day and hour."""
    from gitstats.parser import get_hourly_activity, get_weekly_activity

    # Weekly activity
    weekly = get_weekly_activity(commits)

    console.print("[bold]📅 Activity by Day of Week[/]\n")

    max_commits = max(d["commits"] for d in weekly) if weekly else 1

    for day_stat in weekly:
        bar_width = int((day_stat["commits"] / max_commits) * 30) if max_commits else 0
        bar = "█" * bar_width

        console.print(
            f"  [cyan]{day_stat['day']}[/] │ [green]{bar:<30}[/] {day_stat['commits']:>3} commits"
        )

    console.print()

    # Hourly activity (simplified - peak hours)
    hourly = get_hourly_activity(commits)
    peak_hours = sorted(hourly, key=lambda x: x["commits"], reverse=True)[:3]

    if peak_hours and peak_hours[0]["commits"] > 0:
        console.print("[bold]⏰ Peak Coding Hours[/]\n")
        for h in peak_hours:
            if h["commits"] > 0:
                hour_str = f"{h['hour']:02d}:00"
                console.print(
                    f"  [yellow]{hour_str}[/] - {h['commits']} commits ({h['percentage']:.1f}%)"
                )
        console.print()


def _filter_commits_by_author(commits: list[dict], author: str) -> list[dict]:
    """Filter commits by author name (case-insensitive partial match)."""
    author_lower = author.lower()
    return [c for c in commits if author_lower in c["author"].lower()]


def _filter_commits_by_date(
    commits: list[dict],
    since_date,
    until_date,
) -> list[dict]:
    """Filter commits by date range."""
    filtered = commits

    if since_date:
        filtered = [c for c in filtered if c["date"].replace(tzinfo=None) >= since_date]

    if until_date:
        # Include the entire "until" day
        from datetime import timedelta

        until_end = until_date + timedelta(days=1)
        filtered = [c for c in filtered if c["date"].replace(tzinfo=None) < until_end]

    return filtered


def _print_streaks(streaks: dict) -> None:
    """Print commit streak statistics."""
    console.print("[bold]🔥 Commit Streaks[/]\n")

    current = streaks["current_streak"]
    longest = streaks["longest_streak"]
    active_days = streaks["total_active_days"]

    # Current streak with fire emojis based on length
    if current > 0:
        fires = "🔥" * min(current, 5)
        console.print(f"  [green]Current streak:[/] {current} days {fires}")
    else:
        console.print("  [dim]Current streak:[/] 0 days (no recent commits)")

    console.print(f"  [yellow]Longest streak:[/] {longest} days")
    console.print(f"  [cyan]Total active days:[/] {active_days}")
    console.print()


if __name__ == "__main__":
    app()
