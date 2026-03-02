"""LLM client abstraction supporting both API and CLI backends."""

import json
import re
import shutil
import subprocess

import anthropic


class LLMClient:
    """Base class for LLM backends."""

    def query(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        raise NotImplementedError


class APIClient(LLMClient):
    """Uses the Anthropic Python SDK directly. Requires an API key."""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def query(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text.strip()


class CLIClient(LLMClient):
    """Uses the `claude` CLI subprocess. Works with Claude Max subscription."""

    def __init__(self, model: str = "sonnet"):
        if not shutil.which("claude"):
            raise RuntimeError(
                "claude CLI not found. Install Claude Code first:\n"
                "  npm install -g @anthropic-ai/claude-code"
            )
        self.model = model

    def query(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        cmd = [
            "claude",
            "-p",
            "--output-format", "text",
            "--model", self.model,
            "--system-prompt", system_prompt,
            "--no-session-persistence",
            user_prompt,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"claude CLI failed:\n{result.stderr}")

        return result.stdout.strip()


def strip_markdown_fences(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_json_response(raw: str) -> dict:
    raw = strip_markdown_fences(raw)
    return json.loads(raw)
