"""Code challenge generation using LLM."""

from pydantic import ValidationError

from .llm_client import LLMClient, parse_json_response
from .models import GeneratedChallenge
from .prompts.generate import SYSTEM_PROMPT, build_user_prompt, get_issue_count


def generate_challenge(
    client: LLMClient,
    language: str,
    category: str,
    difficulty: str,
    count: int | None = None,
) -> GeneratedChallenge:
    if count is None:
        count = get_issue_count(difficulty)

    user_prompt = build_user_prompt(language, category, difficulty, count)

    last_error = None
    for attempt in range(3):
        prompt = user_prompt
        if attempt > 0 and last_error:
            prompt += (
                f"\n\nYour previous response had a validation error: {last_error}\n"
                f"Please try again with valid JSON matching the required schema."
            )

        raw = client.query(SYSTEM_PROMPT, prompt, temperature=0.9)

        try:
            data = parse_json_response(raw)
            return GeneratedChallenge.model_validate(data)
        except (ValueError, ValidationError) as e:
            last_error = str(e)

    raise RuntimeError(
        f"Failed to generate valid challenge after 3 attempts. Last error: {last_error}"
    )
