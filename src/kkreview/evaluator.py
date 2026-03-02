"""Review evaluation using LLM."""

import json

from pydantic import ValidationError

from .llm_client import LLMClient, parse_json_response
from .models import EvaluationResult, GeneratedChallenge
from .prompts.evaluate import SYSTEM_PROMPT, build_user_prompt


def evaluate_review(
    client: LLMClient,
    challenge: GeneratedChallenge,
    user_findings: str,
) -> EvaluationResult:
    issues_json = json.dumps(
        [i.model_dump() for i in challenge.issues], indent=2
    )
    user_prompt = build_user_prompt(
        challenge.language, challenge.code, issues_json, user_findings
    )

    last_error = None
    for attempt in range(3):
        prompt = user_prompt
        if attempt > 0 and last_error:
            prompt += (
                f"\n\nYour previous response had a validation error: {last_error}\n"
                f"Please try again with valid JSON matching the required schema."
            )

        raw = client.query(SYSTEM_PROMPT, prompt, temperature=0.2)

        try:
            data = parse_json_response(raw)
            return EvaluationResult.model_validate(data)
        except (ValueError, ValidationError) as e:
            last_error = str(e)

    raise RuntimeError(
        f"Failed to parse evaluation after 3 attempts. Last error: {last_error}"
    )
