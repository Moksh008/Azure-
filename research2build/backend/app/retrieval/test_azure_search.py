import os
import pytest

from app.embeddings.provider import (
    AzureOpenAIEmbeddingProvider,
    HashEmbeddingProvider,
    OllamaEmbeddingProvider,
)
from app.retrieval.azure_search_vector_store import AzureAISearchVectorStore
from app.retrieval.chroma_vector_store import LIBRARY_COLLECTION, ChromaVectorStore
from app.retrieval.evidence import EvidenceChunk
from app.retrieval.factory import (
    get_embedding_provider,
    get_retriever,
    get_vector_store,
)
from app.retrieval.vector_store import InMemoryVectorStore


def test_azure_search_vector_store_unconfigured_fallback():
    store = AzureAISearchVectorStore()
    assert not store.is_configured

    chunk = EvidenceChunk(
        chunk_id="az-chunk-1",
        paper_id="paper-az",
        title="Azure Search Test",
        text="Testing fallback behavior in Azure AISearchVectorStore",
    )

    store.add_chunks([chunk])
    results = store.search("testing fallback behavior", top_k=1)

    assert len(results) == 1
    assert results[0].chunk_id == "az-chunk-1"


def test_azure_search_index_schema():
    store = AzureAISearchVectorStore(
        endpoint="https://demo.search.windows.net",
        api_key="demo-key",
        index_name="test-index",
    )
    assert store.is_configured
    schema = store.get_index_schema(vector_dim=128)

    assert schema["name"] == "test-index"
    field_names = [f["name"] for f in schema["fields"]]
    assert "chunk_id" in field_names
    assert "original_chunk_id" in field_names
    assert "paper_id" in field_names
    assert "title" in field_names
    assert "text" in field_names
    assert "source_url" in field_names
    assert "page_number" in field_names
    assert "section" in field_names
    assert "vector" in field_names


def _clear_retrieval_env(monkeypatch):
    for var in (
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        "OLLAMA_BASE_URL",
        "OLLAMA_EMBEDDING_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)


def test_factory_vector_store_switching(monkeypatch):
    # Unset env vars -> ChromaVectorStore (persistent local default)
    _clear_retrieval_env(monkeypatch)

    store_local = get_vector_store()
    assert isinstance(store_local, ChromaVectorStore)

    # Set env vars -> AzureAISearchVectorStore
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://mysearch.search.windows.net")
    monkeypatch.setenv("AZURE_SEARCH_API_KEY", "secret-key")
    monkeypatch.setenv("AZURE_SEARCH_INDEX", "prod-index")

    store_azure = get_vector_store()
    assert isinstance(store_azure, AzureAISearchVectorStore)
    assert store_azure.is_configured


def test_factory_embedding_provider_precedence(monkeypatch):
    _clear_retrieval_env(monkeypatch)

    # No Azure, no Ollama -> hash fallback
    assert isinstance(get_embedding_provider(), HashEmbeddingProvider)

    # Ollama configured -> OllamaEmbeddingProvider with the local default model
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    provider = get_embedding_provider()
    assert isinstance(provider, OllamaEmbeddingProvider)
    assert provider.model == "nomic-embed-text"

    # Azure configured -> Azure wins over Ollama
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://x.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "key")
    monkeypatch.setenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embed")
    assert isinstance(get_embedding_provider(), AzureOpenAIEmbeddingProvider)


def test_semantic_retriever_gets_discovery_collection(monkeypatch):
    """SemanticRetriever clears its store on every retrieve() — it must get
    the dedicated discovery collection, never the library evidence one."""
    from unittest.mock import MagicMock

    from app.retrieval.semantic_retriever import SemanticRetriever

    _clear_retrieval_env(monkeypatch)

    retriever = SemanticRetriever(openalex_client=MagicMock())
    store = retriever.vector_store

    assert isinstance(store, ChromaVectorStore)
    assert store.collection_name != LIBRARY_COLLECTION
