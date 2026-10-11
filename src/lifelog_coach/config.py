"""从环境变量加载的配置（支持 .env 文件）。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


@dataclass(frozen=True)
class Settings:
    """LLM 接入配置。兼容 OpenAI 协议的任意服务商均可使用。"""

    api_key: str
    base_url: str
    model: str

    @classmethod
    def from_env(cls) -> "Settings":
        """读取环境变量构造配置，缺失时可回落到默认值。"""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        base_url = os.getenv("OPENAI_BASE_URL", "").strip() or DEFAULT_BASE_URL
        model = os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL
        return cls(api_key=api_key, base_url=base_url, model=model)
