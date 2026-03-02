"""Prompt templates for review evaluation."""

import json

from ..models import EvaluationResult, FindingMatch

SYSTEM_PROMPT = """\
You are an expert code reviewer evaluating a student's code review findings.
You will be given:
1. A code snippet with known issues (the answer key)
2. The student's review findings

Your job is to:
- Match each student finding to a known issue (or identify it as a false positive)
- Rate match quality: "precise" (identified issue and root cause correctly), \
"partial" (identified something wrong in the area but missed the root cause), \
"vague" (too general to be actionable)
- Provide constructive, encouraging feedback
- Give specific tips for issues they missed

Scoring:
- precise match: 1.0 point
- partial match: 0.5 points
- vague match: 0.25 points
- false positive: -0.25 points (but total score floor at 0.0)
- Score = sum(points) / total_issues, capped at [0.0, 1.0]

You MUST respond with valid JSON only. No markdown fences, no commentary outside the JSON."""


def build_user_prompt(
    language: str, code: str, issues_json: str, user_findings: str
) -> str:
    # Add line numbers to code
    lines = code.split("\n")
    numbered_code = "\n".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))

    schema = EvaluationResult.model_json_schema()

    return f"""\
## Code Under Review ({language})

{numbered_code}

## Known Issues (Answer Key)
{issues_json}

## Student's Review Findings
{user_findings}

Evaluate the student's review. For each known issue, determine if the student found it \
and rate the quality of their finding. Identify any false positives.

Respond with valid JSON containing:
- "matches": array of objects with "issue_id" (int), "found" (bool), "user_text" (string, \
the relevant part of user's finding or empty), "quality" (string: "precise"/"partial"/"vague")
- "false_positives": array of strings (user findings that don't match any real issue)
- "score": float 0.0-1.0
- "found_count": int (number of issues found with at least partial match)
- "total_count": int (total known issues)
- "feedback": string (overall narrative feedback, 2-3 sentences, encouraging)
- "tips": array of strings (specific improvement tips, one per missed issue)

Respond with JSON only."""
