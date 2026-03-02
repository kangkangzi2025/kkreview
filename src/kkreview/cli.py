"""CLI commands for kkreview."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import CONFIG_KEYS, Config
from .db import Database
from .session import run_session
from .stats import show_stats as _show_stats

console = Console()

app = typer.Typer(
    name="kkreview",
    help="Code review training tool powered by Claude.",
    no_args_is_help=True,
)

config_app = typer.Typer(help="Manage configuration.")
app.add_typer(config_app, name="config")


def version_callback(value: bool):
    if value:
        console.print(f"kkreview {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit.",
    ),
):
    pass


@app.command()
def practice(
    language: Optional[str] = typer.Option(
        None, "--language", "-l",
        help="Target language (python/go/javascript/typescript/rust/c/cpp/java). Default: random.",
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-c",
        help="Issue category (security/performance/logic/quality/design/concurrency). Default: random.",
    ),
    difficulty: str = typer.Option(
        "medium", "--difficulty", "-d",
        help="Difficulty level (easy/medium/hard).",
    ),
    rounds: int = typer.Option(
        0, "--rounds", "-n",
        help="Number of rounds (0 = unlimited, keep going until you quit).",
    ),
):
    """Start a code review practice session."""
    db = Database()
    config = Config(db)

    # Apply defaults from config if not specified
    if language is None:
        language = config.get_default_language()
    if category is None:
        category = config.get_default_category()

    try:
        run_session(db, config, language=language, category=category,
                    difficulty=difficulty, rounds=rounds)
    except KeyboardInterrupt:
        console.print("\n[yellow]Session cancelled.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def stats(
    last: int = typer.Option(10, "--last", "-n", help="Show last N sessions."),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category."),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Filter by language."),
):
    """View your practice progress and statistics."""
    db = Database()
    try:
        _show_stats(db, limit=last, category=category, language=language)
    finally:
        db.close()


@config_app.command("init")
def config_init():
    """Interactive first-time setup."""
    db = Database()
    config = Config(db)

    console.print("[bold]kkreview Configuration Setup[/bold]\n")

    # Backend selection
    console.print("[bold]Choose backend:[/bold]")
    console.print("  [cyan]cli[/cyan]  - Use Claude Code CLI (works with Claude Max subscription, no API key needed)")
    console.print("  [cyan]api[/cyan]  - Use Anthropic API directly (requires API key, pay-per-use)\n")
    backend = typer.prompt("Backend", default="cli")
    config.set("backend", backend)

    # API key (only for api backend)
    if backend == "api":
        existing_key = config.get_api_key()
        if existing_key:
            console.print(f"[green]API key already configured.[/green]")
            overwrite = typer.confirm("Overwrite existing API key?", default=False)
            if overwrite:
                api_key = typer.prompt("Enter your Anthropic API key", hide_input=True)
                config.set("api_key", api_key)
                console.print("[green]API key saved.[/green]")
        else:
            api_key = typer.prompt("Enter your Anthropic API key", hide_input=True)
            config.set("api_key", api_key)
            console.print("[green]API key saved.[/green]")
    else:
        console.print("[green]Using Claude Code CLI — no API key needed.[/green]")

    # Model
    default_model = "sonnet" if backend == "cli" else "claude-sonnet-4-20250514"
    model = typer.prompt(f"Model", default=default_model)
    config.set("model", model)

    # Default language
    lang = typer.prompt(
        "Default language (python/go/javascript/typescript/rust/c/cpp/java/random)",
        default="random",
    )
    if lang != "random":
        config.set("default_language", lang)

    # Default difficulty
    diff = typer.prompt("Default difficulty (easy/medium/hard)", default="medium")
    config.set("default_difficulty", diff)

    console.print("\n[bold green]Configuration complete![/bold green]")
    console.print("Run [bold]kkreview practice[/bold] to start training.")
    db.close()


@config_app.command("set")
def config_set(
    key: str = typer.Argument(help=f"Config key ({', '.join(CONFIG_KEYS)})."),
    value: str = typer.Argument(help="Config value."),
):
    """Set a configuration value."""
    db = Database()
    config = Config(db)
    try:
        config.set(key, value)
        console.print(f"[green]Set {key}.[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@config_app.command("get")
def config_get(
    key: str = typer.Argument(help="Config key to retrieve."),
):
    """Get a configuration value."""
    db = Database()
    config = Config(db)
    all_config = config.get_all()
    if key in all_config:
        console.print(f"{key} = {all_config[key]}")
    else:
        console.print(f"[red]Unknown key: {key}[/red]")
    db.close()


@config_app.command("show")
def config_show():
    """Show all configuration values."""
    db = Database()
    config = Config(db)
    all_config = config.get_all()

    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_column("Description", style="dim")

    for key, desc in CONFIG_KEYS.items():
        value = all_config.get(key, "(not set)")
        table.add_row(key, value, desc)

    console.print(table)
    db.close()
