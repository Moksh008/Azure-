"""Tests for the LLM provider factory (backend/app/services/llm_factory.py).

Verifies the precedence: Azure OpenAI / Azure AI Foundry env vars win over
a plain OpenAI-compatible endpoint, and a clear error is raised when
neither is configured — never a silent fallback that could let /analysis
or /qa run without a real LLM behind them.
"""

import pytest

from backend.app.services.llm_factory import get_llm_service
from backend.app.services.llm_service import AzureFoundryLLMService, LLMService


def _clear_llm_env(monkeypatch):
    for var in [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
        "AZURE_OPENAI_API_VERSION",
        "LLM_ENDPOINT",
        "LLM_API_KEY",
        "LLM_MODEL",
    ]:
        monkeypatch.delenv(var, raising=False)


def test_returns_azure_foundry_service_when_azure_vars_set(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")

    service = get_llm_service()

    assert isinstance(service, AzureFoundryLLMService)
    assert service.endpoint == "https://my-resource.openai.azure.com"
    assert service.deployment == "gpt-4o"
    assert service.api_version == "2024-02-15-preview"


def test_azure_api_version_env_var_overrides_default(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    service = get_llm_service()

    assert service.api_version == "2024-06-01"


def test_falls_back_to_plain_llm_service_when_azure_vars_absent(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    service = get_llm_service()

    assert isinstance(service, LLMService)
    assert service.model == "gpt-4o-mini"


def test_azure_vars_take_precedence_over_plain_llm_vars(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    service = get_llm_service()

    assert isinstance(service, AzureFoundryLLMService)


def test_raises_clear_error_when_nothing_configured(monkeypatch):
    _clear_llm_env(monkeypatch)

    with pytest.raises(RuntimeError, match="No LLM provider configured"):
        get_llm_service()


def test_partial_azure_config_falls_through_to_plain_llm(monkeypatch):
    _clear_llm_env(monkeypatch)
    # Missing AZURE_OPENAI_CHAT_DEPLOYMENT -> Azure branch must not trigger.
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")

    service = get_llm_service()

    assert isinstance(service, LLMService)
