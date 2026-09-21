import os

from app.embeddings.provider import (
    AzureOpenAIEmbeddingProvider,
    EmbeddingProvider,
    HashEmbeddingProvider,
)
from app.retrieval.azure_search_vector_store import AzureAISearchVectorStore
from app.retrieval.openalex_retriever import OpenAlexRetriever
from app.retrieval.retriever import Retriever
from app.retrieval.semantic_retriever import SemanticRetriever
from app.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore


_VECTOR_STORE_CACHE: dict[tuple[str | None, str | None, str | None], BaseVectorStore] = {}


def _vector_store_cache_key() -> tuple[str | None, str | None, str | None]:
    return (
        os.getenv("AZURE_SEARCH_ENDPOINT"),
        os.getenv("AZURE_SEARCH_API_KEY"),
        os.getenv("AZURE_SEARCH_INDEX"),
    )


def get_embedding_provider() -> EmbeddingProvider:
    """Return configured embedding provider instance."""
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    if azure_endpoint and azure_key and azure_deployment:
        return AzureOpenAIEmbeddingProvider(
            endpoint=azure_endpoint,
            api_key=azure_key,
            deployment=azure_deployment,
        )

    return HashEmbeddingProvider()


def get_vector_store(
    embedding_provider: EmbeddingProvider | None = None,
) -> BaseVectorStore:
    """Return configured vector store instance (AzureAISearchVectorStore or InMemoryVectorStore)."""
    cache_key = _vector_store_cache_key()
    if cache_key in _VECTOR_STORE_CACHE:
        return _VECTOR_STORE_CACHE[cache_key]

    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_API_KEY")
    search_index = os.getenv("AZURE_SEARCH_INDEX")

    provider = embedding_provider or get_embedding_provider()

    if search_endpoint and search_key and search_index:
        store = AzureAISearchVectorStore(
            endpoint=search_endpoint,
            api_key=search_key,
            index_name=search_index,
            embedding_provider=provider,
        )
    else:
        store = InMemoryVectorStore(embedding_provider=provider)

    _VECTOR_STORE_CACHE[cache_key] = store
    return store


def get_retriever(use_semantic: bool = True) -> Retriever:
    """
    Factory function providing a configured Retriever instance.
    Defaults to SemanticRetriever using configured vector store and embedding provider.
    """
    if not use_semantic:
        return OpenAlexRetriever()

    provider = get_embedding_provider()
    store = get_vector_store(embedding_provider=provider)

    return SemanticRetriever(
        embedding_provider=provider,
        vector_store=store,
    )
