import pytest

from app.agents.llm_client import LLMProvider
from app.core.config import settings


@pytest.mark.parametrize("provider", ["offline", "mock", " OFFLINE "])
def test_local_provider_never_creates_remote_client(monkeypatch, provider):
    monkeypatch.setattr(settings, "AI_PROVIDER", provider)
    client = LLMProvider()
    client.api_key = "test-key"
    assert not client.is_configured()
    assert client.get_client() is None


def test_gemini_provider_remains_configured(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    client = LLMProvider()
    client.api_key = "test-key"
    assert client.is_configured()
