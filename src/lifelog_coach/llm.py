"""面向任意 OpenAI 兼容 chat 接口的轻量封装。"""

from __future__ import annotations

from openai import OpenAI

from .config import Settings


class LLM:
    def __init__(self, settings: Settings | None = None) -> None:
        # 未显式传入配置时，自动从环境变量 / .env 读取。
        self.settings = settings or Settings.from_env()
        self._client = OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
        )

    def complete(self, system: str, user: str) -> str:
        """发起一次 chat 请求并返回 assistant 的文本内容。"""
        resp = self._client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return (resp.choices[0].message.content or "").strip()
