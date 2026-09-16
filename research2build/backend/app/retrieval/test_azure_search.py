import os
import pytest

from app.retrieval.azure_search_vector_store import AzureAISearchVectorStore
from app.retrieval.evidence import EvidenceChunk
from app.retrieval.factory import get_retriever, get_vector_store
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


def test_factory_vector_store_switching(monkeypatch):
    # Unset env vars -> InMemoryVectorStore
    monkeypatch.delenv("AZURE_SEARCH_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_SEARCH_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_SEARCH_INDEX", raising=False)

    store_local = get_vector_store()
    assert isinstance(store_local, InMemoryVectorStore)

    # Set env vars -> AzureAISearchVectorStore
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://mysearch.search.windows.net")
    monkeypatch.setenv("AZURE_SEARCH_API_KEY", "secret-key")
    monkeypatch.setenv("AZURE_SEARCH_INDEX", "prod-index")

    store_azure = get_vector_store()
    assert isinstance(store_azure, AzureAISearchVectorStore)
    assert store_azure.is_configured
