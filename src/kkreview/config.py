"""Configuration management for kkreview."""

import os

from .db import Database


CONFIG_KEYS = {
    "backend": "Backend to use: 'api' (Anthropic API key) or 'cli' (Claude Code / Max subscription)",
    "api_key": "Anthropic API key (only needed for 'api' backend)",
    "model": "Claude model (default: claude-sonnet-4-20250514 for api, sonnet for cli)",
    "theme": "Syntax highlight theme (default: github-light). Try: vs, xcode, solarized-light, monokai",
    "default_language": "Default language for practice (default: random)",
    "default_difficulty": "Default difficulty (default: medium)",
    "default_category": "Default category (default: random)",
}


class Config:
    def __init__(self, db: Database):
        self.db = db

    def get_backend(self) -> str:
        return self.db.get_config("backend", "cli")

    def get_api_key(self) -> str | None:
        return os.environ.get("ANTHROPIC_API_KEY") or self.db.get_config("api_key")

    def get_model(self) -> str:
        backend = self.get_backend()
        default = "sonnet" if backend == "cli" else "claude-sonnet-4-20250514"
        return self.db.get_config("model", default)

    def get_default_language(self) -> str:
        return self.db.get_config("default_language", "random")

    def get_default_difficulty(self) -> str:
        return self.db.get_config("default_difficulty", "medium")

    def get_default_category(self) -> str:
        return self.db.get_config("default_category", "random")

    def get_theme(self) -> str:
        return self.db.get_config("theme", "github-light")

    def set(self, key: str, value: str):
        if key not in CONFIG_KEYS:
            raise ValueError(f"Unknown config key: {key}. Valid keys: {', '.join(CONFIG_KEYS)}")
        self.db.set_config(key, value)

    def get_all(self) -> dict[str, str]:
        result = {}
        stored = self.db.get_all_config()
        for key in CONFIG_KEYS:
            if key == "api_key":
                env_val = os.environ.get("ANTHROPIC_API_KEY")
                if env_val:
                    result[key] = env_val[:8] + "..." + env_val[-4:]
                elif key in stored:
                    result[key] = stored[key][:8] + "..." + stored[key][-4:]
                else:
                    result[key] = "(not set)"
            elif key == "backend":
                result[key] = stored.get(key, "cli")
            else:
                result[key] = stored.get(key, "(default)")
        return result
