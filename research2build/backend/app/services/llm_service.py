import httpx


def _build_messages(prompt: str, system_prompt: str | None) -> list[dict]:
    messages = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    return messages


def _extract_content(data: dict, provider_label: str) -> str:
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"{provider_label} returned an unexpected response format"
        ) from exc


class LLMService:
    """
    Small wrapper around a plain OpenAI-compatible chat completion API
    (OpenAI itself, or any self-hosted server that mirrors its shape).

    Analyzer and Q&A use this service instead of calling the LLM provider
    directly. Prefer AzureFoundryLLMService when talking to Azure OpenAI /
    Azure AI Foundry, which uses a different auth scheme and URL shape.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        timeout: float = 60.0,
        reasoning_effort: str | None = None,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        # Reasoning models (Qwen3 via Ollama, OpenAI o-series, ...) can spend
        # most of their latency on a hidden "thinking" pass before the real
        # content. Left unset by default (real OpenAI chat models don't
        # accept this field); set LLM_REASONING_EFFORT=none for local Ollama
        # models to skip that pass entirely — cuts local response time from
        # ~30-40s to ~1-2s with no change in output quality for these
        # short, deterministic JSON-extraction prompts.
        self.reasoning_effort = reasoning_effort

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": _build_messages(prompt, system_prompt),
            "temperature": temperature,
        }
        if self.reasoning_effort is not None:
            payload["reasoning_effort"] = self.reasoning_effort

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise RuntimeError(f"LLM API request failed: {exc}") from exc

        return _extract_content(response.json(), "LLM API")


class AzureFoundryLLMService:
    """
    Chat completion client for Azure OpenAI / Azure AI Foundry model
    deployments.

    Same public interface as LLMService (a single `generate()` method) so
    PaperAnalyzer and GroundedQA need no changes to use either provider —
    only the factory in llm_factory.py decides which one gets built, based
    on which environment variables are set.

    Azure's request shape differs from plain OpenAI: the model deployment
    is part of the URL (not the payload), auth uses an `api-key` header
    instead of `Authorization: Bearer`, and requests carry an explicit
    `api-version` query parameter.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str = "2024-02-15-preview",
        timeout: float = 60.0,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        url = (
            f"{self.endpoint}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )
        payload = {
            "messages": _build_messages(prompt, system_prompt),
            "temperature": temperature,
        }
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise RuntimeError(f"Azure AI Foundry request failed: {exc}") from exc

        return _extract_content(response.json(), "Azure AI Foundry")
