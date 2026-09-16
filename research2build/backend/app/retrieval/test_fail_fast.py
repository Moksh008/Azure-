import pytest

from app.embeddings.provider import AzureOpenAIEmbeddingProvider
from app.retrieval.azure_search_vector_store import AzureAISearchVectorStore


def test_azure_openai_fail_fast_when_fallback_disabled():
    provider = AzureOpenAIEmbeddingProvider(allow_fallback=False)
    with pytest.raises(
        RuntimeError, match="Azure OpenAI embedding credentials missing"
    ):
        provider.embed("test query")


def test_azure_search_fail_fast_when_fallback_disabled():
    store = AzureAISearchVectorStore(allow_fallback=False)
    assert not store.is_configured

    with pytest.raises(
        RuntimeError, match="Azure AI Search credentials missing"
    ):
        store.search("test query")
