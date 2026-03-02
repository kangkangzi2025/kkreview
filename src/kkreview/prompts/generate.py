"""Prompt templates for code challenge generation."""

import json

from ..models import GeneratedChallenge, HiddenIssue

SYSTEM_PROMPT = """\
You are an expert code reviewer and security researcher. Your task is to generate \
realistic code snippets that contain specific, intentional issues for code review \
training purposes.

Rules:
1. The code must look realistic -- like something a mid-level developer might write \
in a real project. It should have a clear purpose (e.g., "user authentication endpoint", \
"file upload handler", "cache invalidation logic").
2. The code must be syntactically valid and would compile/run (aside from the issues).
3. Issues must be SUBTLE -- not obvious syntax errors. They should be the kind of \
thing that slips past a cursory review.
4. Each issue must be on specific, identifiable lines.
5. Include some perfectly fine code too -- not every line should be problematic.
6. The code length should match the difficulty level.
7. The ONLY issues in the code are the ones you list. Do not embed unlisted issues.

You MUST respond with valid JSON only. No markdown fences, no commentary outside the JSON."""


def build_user_prompt(language: str, category: str, difficulty: str, count: int) -> str:
    difficulty_guide = {
        "easy": (
            "Issues are relatively straightforward (e.g., obvious SQL injection, clear "
            "null dereference). Code is 40-60 lines. Issues should be findable by someone "
            "with basic review experience."
        ),
        "medium": (
            "Issues require careful reading (e.g., subtle race condition, non-obvious "
            "path traversal, tricky off-by-one). Code is 60-90 lines. Include a mix of "
            "obvious and subtle issues."
        ),
        "hard": (
            "Issues are deeply buried, may involve interaction between components, or "
            "require domain knowledge. Code is 80-120 lines. Include at least one red "
            "herring (code that looks suspicious but is actually fine)."
        ),
    }

    schema = GeneratedChallenge.model_json_schema()
    issue_schema = HiddenIssue.model_json_schema()

    return f"""\
Generate a {language} code snippet for review training.

Difficulty: {difficulty}
Category focus: {category} (at least half the issues should be from this category, \
others can be from any category)
Number of issues to embed: {count}

Difficulty guidelines for "{difficulty}":
{difficulty_guide[difficulty]}

Each issue object must have these fields:
{json.dumps(issue_schema['properties'], indent=2)}

Severity values: "critical", "major", "minor"

The complete response must be valid JSON with these top-level fields:
- "language": the programming language (string)
- "title": short description of what the code does (string)
- "context": brief scenario description, 1-2 sentences (string)
- "code": the full code snippet (string)
- "issues": array of issue objects

Respond with JSON only."""


def get_issue_count(difficulty: str) -> int:
    return {"easy": 2, "medium": 3, "hard": 5}[difficulty]
