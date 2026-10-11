import pytest

from lifelog_coach import config
from lifelog_coach.config import Settings


def test_from_env_defaults(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    s = Settings.from_env()
    assert s.api_key == "k"
    assert s.base_url == config.DEFAULT_BASE_URL
    assert s.model == config.DEFAULT_MODEL


def test_from_env_overrides(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-x")
    s = Settings.from_env()
    assert s.base_url == "https://example.com/v1"
    assert s.model == "gpt-x"


def test_from_env_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None)
    with pytest.raises(RuntimeError):
        Settings.from_env()
