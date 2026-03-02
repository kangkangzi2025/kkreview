"""Rich terminal display helpers for kkreview."""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .models import EvaluationResult, GeneratedChallenge

console = Console()


def show_challenge_header(challenge: GeneratedChallenge, difficulty: str):
    header = Text()
    header.append("CODE REVIEW CHALLENGE\n", style="bold white")
    header.append(f"Language: ", style="dim")
    header.append(f"{challenge.language}", style="bold cyan")
    header.append(f"  |  Difficulty: ", style="dim")
    difficulty_colors = {"easy": "green", "medium": "yellow", "hard": "red"}
    header.append(f"{difficulty}", style=f"bold {difficulty_colors.get(difficulty, 'white')}")
    header.append(f"\n\n", style="dim")
    header.append(f"{challenge.title}\n", style="bold")
    header.append(f"{challenge.context}", style="italic dim")

    console.print(Panel(header, border_style="blue", padding=(1, 2)))


def show_code(code: str, language: str, theme: str = "github-light"):
    syntax = Syntax(
        code,
        language,
        theme=theme,
        line_numbers=True,
        padding=1,
        background_color="default",
    )
    console.print(Panel(syntax, title="[bold]Code to Review[/bold]", border_style="cyan"))


def show_results(challenge: GeneratedChallenge, evaluation: EvaluationResult):
    # Score header
    score_pct = int(evaluation.score * 100)
    if score_pct >= 80:
        score_style = "bold green"
    elif score_pct >= 50:
        score_style = "bold yellow"
    else:
        score_style = "bold red"

    header = Text()
    header.append(f"RESULTS: ", style="bold white")
    header.append(f"{evaluation.found_count}/{evaluation.total_count}", style=score_style)
    header.append(f" issues found  |  Score: ", style="bold white")
    header.append(f"{score_pct}%", style=score_style)

    if score_pct == 100:
        header.append(f"\nPERFECT SCORE!", style="bold green")

    console.print(Panel(header, border_style="blue", padding=(1, 2)))

    # Issues table
    table = Table(title="Issue Breakdown", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Category", style="cyan")
    table.add_column("Severity", width=10)
    table.add_column("Lines", width=10)
    table.add_column("Status", width=10)
    table.add_column("Your Finding", max_width=50)

    matches_by_id = {m.issue_id: m for m in evaluation.matches}

    for issue in challenge.issues:
        match = matches_by_id.get(issue.id)
        if match and match.found:
            quality_styles = {
                "precise": ("FOUND", "bold green"),
                "partial": ("PARTIAL", "bold yellow"),
                "vague": ("VAGUE", "bold yellow"),
            }
            status_text, status_style = quality_styles.get(
                match.quality, ("FOUND", "bold green")
            )
            user_text = match.user_text[:50] if match.user_text else "--"
        else:
            status_text = "MISSED"
            status_style = "bold red"
            user_text = "--"

        severity_styles = {
            "critical": "bold red",
            "major": "bold yellow",
            "minor": "dim",
        }

        lines = f"{issue.line_start}"
        if issue.line_end != issue.line_start:
            lines = f"{issue.line_start}-{issue.line_end}"

        table.add_row(
            str(issue.id),
            issue.category,
            Text(issue.severity, style=severity_styles.get(issue.severity, "")),
            lines,
            Text(status_text, style=status_style),
            user_text,
        )

    console.print(table)

    # Show missed issue explanations
    for issue in challenge.issues:
        match = matches_by_id.get(issue.id)
        if not match or not match.found:
            explanation = Text()
            explanation.append(f"MISSED: ", style="bold red")
            explanation.append(f"{issue.subcategory}", style="bold")
            explanation.append(f" (Lines {issue.line_start}-{issue.line_end})\n", style="dim")
            explanation.append(f"Severity: {issue.severity}\n\n", style="dim")
            explanation.append(f"{issue.description}\n\n")
            explanation.append(f"{issue.explanation}", style="italic")
            console.print(Panel(explanation, border_style="red", padding=(1, 2)))

    # False positives
    if evaluation.false_positives:
        fp_text = Text()
        fp_text.append("False Positives:\n", style="bold yellow")
        for fp in evaluation.false_positives:
            fp_text.append(f"  - {fp}\n", style="dim")
        console.print(Panel(fp_text, border_style="yellow", padding=(0, 2)))

    # Feedback
    console.print(Panel(evaluation.feedback, title="[bold]Feedback[/bold]", border_style="green"))

    # Tips
    if evaluation.tips:
        tips_text = Text()
        for i, tip in enumerate(evaluation.tips, 1):
            tips_text.append(f"  {i}. {tip}\n")
        console.print(Panel(tips_text, title="[bold]Tips for Improvement[/bold]", border_style="cyan"))


def show_round_summary(round_num: int, evaluation: EvaluationResult, past_results: list[EvaluationResult]):
    """Show a brief summary after each round with running progress."""
    score_pct = int(evaluation.score * 100)
    avg_pct = int(sum(e.score for e in past_results) / len(past_results) * 100)
    total_found = sum(e.found_count for e in past_results)
    total_issues = sum(e.total_count for e in past_results)

    text = Text()
    text.append(f"Round {round_num} complete", style="bold")
    text.append(f"  |  This round: ", style="dim")
    text.append(f"{score_pct}%", style=_score_style(score_pct))
    text.append(f"  |  Running avg: ", style="dim")
    text.append(f"{avg_pct}%", style=_score_style(avg_pct))
    text.append(f"  |  Total: ", style="dim")
    text.append(f"{total_found}/{total_issues} issues found", style="bold")

    console.print(Panel(text, border_style="magenta", padding=(0, 2)))


def show_session_summary(results: list[EvaluationResult]):
    """Show a summary table at the end of a multi-round session."""
    total_found = sum(e.found_count for e in results)
    total_issues = sum(e.total_count for e in results)
    avg_score = sum(e.score for e in results) / len(results)
    avg_pct = int(avg_score * 100)
    best_pct = int(max(e.score for e in results) * 100)

    # Header
    header = Text()
    header.append("SESSION COMPLETE\n\n", style="bold")
    header.append(f"  Rounds:        ", style="dim")
    header.append(f"{len(results)}\n", style="bold")
    header.append(f"  Issues found:  ", style="dim")
    header.append(f"{total_found}/{total_issues}\n", style="bold")
    header.append(f"  Average score: ", style="dim")
    header.append(f"{avg_pct}%\n", style=_score_style(avg_pct))
    header.append(f"  Best round:    ", style="dim")
    header.append(f"{best_pct}%", style=_score_style(best_pct))
    console.print(Panel(header, border_style="blue", padding=(1, 2)))

    # Per-round breakdown
    table = Table(title="Round Breakdown")
    table.add_column("Round", style="dim", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Found", justify="right")
    table.add_column("Missed", justify="right")
    table.add_column("False+", justify="right")

    for i, e in enumerate(results, 1):
        pct = int(e.score * 100)
        table.add_row(
            str(i),
            Text(f"{pct}%", style=_score_style(pct)),
            str(e.found_count),
            str(e.total_count - e.found_count),
            str(len(e.false_positives)),
        )

    console.print(table)


def _score_style(pct: int) -> str:
    if pct >= 80:
        return "bold green"
    elif pct >= 50:
        return "bold yellow"
    return "bold red"


def show_stats_summary(session_count: int, avg_score: float | None, best_score: float | None):
    header = Text()
    header.append("Overall Progress\n", style="bold white")
    header.append(f"Sessions completed: ", style="dim")
    header.append(f"{session_count}\n", style="bold")
    header.append(f"Average score:      ", style="dim")
    if avg_score is not None:
        header.append(f"{int(avg_score * 100)}%\n", style="bold")
    else:
        header.append(f"--\n", style="dim")
    header.append(f"Best score:         ", style="dim")
    if best_score is not None:
        header.append(f"{int(best_score * 100)}%", style="bold green")
    else:
        header.append(f"--", style="dim")

    console.print(Panel(header, border_style="blue", padding=(1, 2)))


def show_category_breakdown(categories: list[dict]):
    table = Table(title="Category Breakdown")
    table.add_column("Category", style="cyan")
    table.add_column("Accuracy", justify="right")
    table.add_column("Tested", justify="right", style="dim")
    table.add_column("Found", justify="right")

    for cat in categories:
        accuracy = cat["accuracy"]
        if accuracy >= 80:
            acc_style = "bold green"
        elif accuracy >= 50:
            acc_style = "bold yellow"
        else:
            acc_style = "bold red"

        table.add_row(
            cat["category"],
            Text(f"{accuracy}%", style=acc_style),
            str(cat["tested"]),
            str(cat["found"]),
        )

    console.print(table)


def show_recent_sessions(sessions: list[dict]):
    table = Table(title="Recent Sessions")
    table.add_column("Date", style="dim")
    table.add_column("Language", style="cyan")
    table.add_column("Category")
    table.add_column("Difficulty")
    table.add_column("Score", justify="right")
    table.add_column("Found", justify="right")

    for s in sessions:
        score = int(s["score"] * 100)
        if score >= 80:
            score_style = "bold green"
        elif score >= 50:
            score_style = "bold yellow"
        else:
            score_style = "bold red"

        difficulty_styles = {"easy": "green", "medium": "yellow", "hard": "red"}

        table.add_row(
            s["created_at"][:16],
            s["language"],
            s["category"],
            Text(s["difficulty"], style=difficulty_styles.get(s["difficulty"], "")),
            Text(f"{score}%", style=score_style),
            f"{s['found_count']}/{s['total_count']}",
        )

    console.print(table)
