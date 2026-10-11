"""Thin wrapper over any OpenAI-compatible chat endpoint."""

from __future__ import annotations

from openai import OpenAI

from .config import Settings


class LLM:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self._client = OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
        )

    def complete(self, system: str, user: str) -> str:
        """Send one chat request and return the assistant text."""
        resp = self._client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return (resp.choices[0].message.content or "").strip()
