import httpx

from backend.app.services.llm_service import LLMService


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