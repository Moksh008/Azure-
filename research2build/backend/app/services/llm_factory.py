"""LLM provider selection, mirroring retrieval/factory.py's pattern for
embeddings and vector stores: read env vars, return the right concrete
implementation, keep the choice invisible to callers (PaperAnalyzer,
GroundedQA only ever call `.generate()`).

Precedence:
1. Azure OpenAI / Azure AI Foundry, if AZURE_OPENAI_ENDPOINT,
   AZURE_OPENAI_API_KEY, and AZURE_OPENAI_CHAT_DEPLOYMENT are all set.
2. A plain OpenAI-compatible endpoint, if LLM_ENDPOINT, LLM_API_KEY, and
   LLM_MODEL are all set (OpenAI itself, or a self-hosted server that
   mirrors its API shape).
3. Otherwise, fail loudly and say exactly which env vars are missing —
   never silently degrade Q&A/analysis to fabricated output.
"""

from __future__ import annotations

import os

from backend.app.services.azure_endpoints import resource_host
from backend.app.services.llm_service import AzureFoundryLLMService, LLMService


def get_llm_service() -> LLMService | AzureFoundryLLMService:
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    if azure_endpoint and azure_key and azure_deployment:
        return AzureFoundryLLMService(
            endpoint=resource_host(azure_endpoint),
            api_key=azure_key,
            deployment=azure_deployment,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
        )

    llm_endpoint = os.getenv("LLM_ENDPOINT")
    llm_key = os.getenv("LLM_API_KEY")
    llm_model = os.getenv("LLM_MODEL")

    if llm_endpoint and llm_key and llm_model:
        # Local models (Ollama, LM Studio, ...) run on CPU/consumer GPU and
        # can take well over LLMService's 60s default for longer prompts
        # (e.g. the 8-field paper analysis) — override via LLM_TIMEOUT_SECONDS
        # if needed, default generously for local inference.
        timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "180"))
        return LLMService(
            endpoint=llm_endpoint,
            api_key=llm_key,
            model=llm_model,
            timeout=timeout,
            reasoning_effort=os.getenv("LLM_REASONING_EFFORT"),
        )

    raise RuntimeError(
        "No LLM provider configured. Set AZURE_OPENAI_ENDPOINT, "
        "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_CHAT_DEPLOYMENT for Azure "
        "AI Foundry, or LLM_ENDPOINT, LLM_API_KEY, and LLM_MODEL for a "
        "plain OpenAI-compatible endpoint."
    )
