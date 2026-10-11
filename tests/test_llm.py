from types import SimpleNamespace

from lifelog_coach import llm as llm_mod
from lifelog_coach.config import Settings


def test_complete_wires_request_and_strips(monkeypatch):
    captured: dict = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["init"] = kwargs

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured["create"] = kwargs
                    msg = SimpleNamespace(content="  hello  ")
                    return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    monkeypatch.setattr(llm_mod, "OpenAI", FakeClient)
    settings = Settings(api_key="k", base_url="https://x", model="m")

    out = llm_mod.LLM(settings).complete("sys", "usr")

    assert out == "hello"
    assert captured["init"] == {"api_key": "k", "base_url": "https://x"}
    assert captured["create"]["model"] == "m"
    assert captured["create"]["messages"][0] == {"role": "system", "content": "sys"}
    assert captured["create"]["messages"][1] == {"role": "user", "content": "usr"}
