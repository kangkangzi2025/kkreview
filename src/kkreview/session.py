"""Practice session orchestration for kkreview."""

import random
import sys
import time

from rich.console import Console
from rich.rule import Rule

from .config import Config
from .db import Database
from .display import (
    show_challenge_header, show_code, show_results,
    show_round_summary, show_session_summary,
)
from .evaluator import evaluate_review
from .generator import generate_challenge
from .llm_client import APIClient, CLIClient, LLMClient
from .models import Category, EvaluationResult, Language

console = Console()


def create_client(config: Config) -> LLMClient:
    backend = config.get_backend()
    model = config.get_model()

    if backend == "cli":
        return CLIClient(model=model)
    else:
        api_key = config.get_api_key()
        if not api_key:
            console.print(
                "[bold red]No API key configured.[/bold red]\n"
                "Run [bold]kkreview config init[/bold] or set the "
                "[bold]ANTHROPIC_API_KEY[/bold] environment variable.\n\n"
                "[dim]Or switch to CLI backend (uses Claude Max subscription):[/dim]\n"
                "  [bold]kkreview config set backend cli[/bold]",
            )
            sys.exit(1)
        return APIClient(api_key=api_key, model=model)


def pick_weighted_category(db: Database) -> str:
    stats = db.get_category_summary()
    categories = list(Category)

    if not stats:
        return random.choice(categories).value

    stats_by_cat = {s["category"]: s["accuracy"] for s in stats}
    weights = []
    for cat in categories:
        accuracy = stats_by_cat.get(cat.value)
        if accuracy is None:
            weights.append(3.0)
        else:
            weights.append(max(0.5, 200.0 - accuracy))
    return random.choices(categories, weights=weights, k=1)[0].value


def pick_random_language() -> str:
    return random.choice(list(Language)).value


def collect_user_findings() -> str:
    console.print(
        "\n[bold]Enter your review findings below.[/bold]",
        style="cyan",
    )
    console.print(
        "List each issue you found (one per line). "
        "When done, press [bold]Ctrl+D[/bold] (or [bold]Ctrl+Z[/bold] on Windows) on an empty line.\n",
        style="dim",
    )

    lines = []
    try:
        while True:
            line = input("  > ")
            lines.append(line)
    except EOFError:
        pass

    findings = "\n".join(lines).strip()
    if not findings:
        console.print("[yellow]No findings submitted. Submitting empty review.[/yellow]")
        findings = "(No issues found)"
    return findings


def ask_continue() -> bool:
    console.print()
    try:
        answer = input("  Continue to next round? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("", "y", "yes")


def run_one_round(
    client: LLMClient,
    db: Database,
    config: Config,
    language: str,
    category: str,
    difficulty: str,
    round_num: int,
    total_rounds: int | None,
) -> EvaluationResult:
    """Run a single review round. Returns the evaluation result."""
    # Round header
    if total_rounds:
        console.print(Rule(f"[bold] Round {round_num}/{total_rounds} [/bold]"))
    else:
        console.print(Rule(f"[bold] Round {round_num} [/bold]"))

    # Resolve per-round language and category
    round_lang = pick_random_language() if language == "random" else language
    round_cat = pick_weighted_category(db) if category == "random" else category

    # Generate
    with console.status("[bold blue]Generating code review challenge...[/bold blue]"):
        challenge = generate_challenge(client, round_lang, round_cat, difficulty)

    # Show
    theme = config.get_theme()
    show_challenge_header(challenge, difficulty)
    show_code(challenge.code, challenge.language, theme=theme)

    # Collect
    start_time = time.time()
    user_findings = collect_user_findings()
    duration_secs = int(time.time() - start_time)

    # Evaluate
    with console.status("[bold blue]Evaluating your review...[/bold blue]"):
        evaluation = evaluate_review(client, challenge, user_findings)

    # Show results
    console.print()
    show_results(challenge, evaluation)

    # Save
    db.save_session(
        challenge=challenge,
        difficulty=difficulty,
        user_findings=user_findings,
        evaluation=evaluation,
        duration_secs=duration_secs,
    )

    # Update category stats
    matches_by_id = {m.issue_id: m for m in evaluation.matches}
    for issue in challenge.issues:
        match = matches_by_id.get(issue.id)
        found = match.found if match else False
        db.update_category_stats(issue.category, issue.subcategory, found)

    return evaluation


def run_session(
    db: Database,
    config: Config,
    language: str | None = None,
    category: str | None = None,
    difficulty: str = "medium",
    rounds: int = 0,
):
    client = create_client(config)

    # Normalize
    if not language:
        language = "random"
    if not category:
        category = "random"

    round_results: list[EvaluationResult] = []
    round_num = 0

    while True:
        round_num += 1

        # Check if we've reached the target number of rounds
        if rounds > 0 and round_num > rounds:
            break

        evaluation = run_one_round(
            client, db, config, language, category, difficulty,
            round_num=round_num,
            total_rounds=rounds if rounds > 0 else None,
        )
        round_results.append(evaluation)

        # Show running progress
        show_round_summary(round_num, evaluation, round_results)

        # If fixed rounds and we've done them all, stop
        if rounds > 0 and round_num >= rounds:
            break

        # Otherwise ask to continue
        if not ask_continue():
            break

    # Session summary
    if len(round_results) > 1:
        console.print()
        show_session_summary(round_results)

    console.print(
        f"\n[dim]All sessions saved. Run [bold]kkreview stats[/bold] to see your progress.[/dim]"
    )
