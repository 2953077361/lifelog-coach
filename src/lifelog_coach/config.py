"""Configuration loaded from the environment (with .env support)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


@dataclass(frozen=True)
class Settings:
    """LLM endpoint settings. Any OpenAI-compatible provider works."""

    api_key: str
    base_url: str
    model: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        base_url = os.getenv("OPENAI_BASE_URL", "").strip() or DEFAULT_BASE_URL
        model = os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL
        return cls(api_key=api_key, base_url=base_url, model=model)
