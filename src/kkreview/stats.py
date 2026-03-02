"""Statistics computation and display for kkreview."""

from rich.console import Console

from .db import Database
from .display import show_category_breakdown, show_recent_sessions, show_stats_summary

console = Console()


def show_stats(
    db: Database,
    limit: int = 10,
    category: str | None = None,
    language: str | None = None,
):
    session_count = db.get_session_count()

    if session_count == 0:
        console.print(
            "[yellow]No practice sessions yet.[/yellow]\n"
            "Run [bold]kkreview practice[/bold] to start training!"
        )
        return

    avg_score = db.get_average_score()
    best_score = db.get_best_score()

    show_stats_summary(session_count, avg_score, best_score)

    # Category breakdown
    categories = db.get_category_summary()
    if categories:
        console.print()
        show_category_breakdown(categories)

    # Recent sessions
    sessions = db.get_sessions(limit=limit, category=category, language=language)
    if sessions:
        console.print()
        show_recent_sessions(sessions)
