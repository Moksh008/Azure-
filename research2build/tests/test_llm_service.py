import httpx

from backend.app.services.llm_service import AzureFoundryLLMService, LLMService


def test_llm_service_generate(monkeypatch):
    def mock_post(*args, **kwargs):
        return httpx.Response(
            200,
            request=httpx.Request("POST", args[0]),
            json={
                "choices": [
                    {
                        "message": {
                            "content": "This is a test response."
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    service = LLMService(
        endpoint="https://example.com/v1/chat/completions",
        api_key="test-key",
        model="test-model",
    )

    result = service.generate(
        prompt="Explain RAG.",
        system_prompt="You are a helpful AI assistant.",
    )

    assert result == "This is a test response."


def test_llm_service_raises_on_unexpected_response(monkeypatch):
    def mock_post(*args, **kwargs):
        return httpx.Response(
            200,
            request=httpx.Request("POST", args[0]),
            json={"unexpected": "shape"},
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    service = LLMService(
        endpoint="https://example.com/v1/chat/completions",
        api_key="test-key",
        model="test-model",
    )

    try:
        service.generate(prompt="Explain RAG.")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "unexpected response format" in str(exc)


def test_azure_foundry_llm_service_generate_uses_azure_url_and_headers(monkeypatch):
    captured = {}

    def mock_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "choices": [
                    {"message": {"content": "Azure Foundry response."}}
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    service = AzureFoundryLLMService(
        endpoint="https://my-resource.openai.azure.com/",
        api_key="azure-test-key",
        deployment="gpt-4o",
        api_version="2024-02-15-preview",
    )

    result = service.generate(
        prompt="Explain RAG.",
        system_prompt="You are a helpful AI assistant.",
    )

    assert result == "Azure Foundry response."
    assert captured["url"] == (
        "https://my-resource.openai.azure.com/openai/deployments/gpt-4o"
        "/chat/completions?api-version=2024-02-15-preview"
    )
    assert captured["headers"]["api-key"] == "azure-test-key"
    assert "Authorization" not in captured["headers"]
    assert captured["json"]["messages"] == [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Explain RAG."},
    ]
    # Azure's payload has no top-level "model" field — the deployment is
    # already fixed by the URL.
    assert "model" not in captured["json"]


def test_azure_foundry_llm_service_raises_on_http_error(monkeypatch):
    def mock_post(*args, **kwargs):
        request = httpx.Request("POST", args[0] if args else kwargs.get("url"))
        return httpx.Response(500, request=request, json={"error": "boom"})

    monkeypatch.setattr(httpx, "post", mock_post)

    service = AzureFoundryLLMService(
        endpoint="https://my-resource.openai.azure.com",
        api_key="azure-test-key",
        deployment="gpt-4o",
    )

    try:
        service.generate(prompt="Explain RAG.")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "Azure AI Foundry request failed" in str(exc)