"""Command-line interface for gitstats."""

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
) -> None:
    """Show commit statistics for a git repository."""
    from gitstats.parser import get_commit_stats
    
    console.print(f"\n[bold]📊 Git Statistics for:[/] [cyan]{path}[/]\n")
    
    stats = get_commit_stats(path)
    
    if not stats:
        console.print("[red]No commits found or not a git repository.[/]")
        raise typer.Exit(1)
    
    console.print(f"[bold]Total commits:[/] [green]{stats['total_commits']}[/]")
    console.print(f"[bold]Contributors:[/] [green]{stats['total_authors']}[/]")
    console.print(f"[bold]First commit:[/] [yellow]{stats['first_commit']}[/]")
    console.print(f"[bold]Latest commit:[/] [yellow]{stats['last_commit']}[/]")
    console.print()
    
    # Show author breakdown table
    if stats.get("author_stats"):
        _print_author_table(stats["author_stats"])


def _print_author_table(author_stats: list[dict]) -> None:
    """Print a table of author statistics."""
    table = Table(title="👥 Commits by Author", show_header=True, header_style="bold cyan")
    
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


if __name__ == "__main__":
    app()
