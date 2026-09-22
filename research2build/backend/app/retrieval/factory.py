import os

from app.embeddings.provider import (
    AzureOpenAIEmbeddingProvider,
    EmbeddingProvider,
    HashEmbeddingProvider,
    OllamaEmbeddingProvider,
)
from app.retrieval.azure_search_vector_store import AzureAISearchVectorStore
from app.retrieval.chroma_vector_store import DISCOVERY_COLLECTION, ChromaVectorStore
from app.retrieval.openalex_retriever import OpenAlexRetriever
from app.retrieval.retriever import Retriever
from app.retrieval.semantic_retriever import SemanticRetriever
from app.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore


_VECTOR_STORE_CACHE: dict[tuple, BaseVectorStore] = {}


def _vector_store_cache_key() -> tuple:
    return (
        os.getenv("AZURE_SEARCH_ENDPOINT"),
        os.getenv("AZURE_SEARCH_API_KEY"),
        os.getenv("AZURE_SEARCH_INDEX"),
        os.getenv("OLLAMA_BASE_URL"),
        os.getenv("OLLAMA_EMBEDDING_MODEL"),
        os.getenv("AZURE_OPENAI_ENDPOINT"),
        os.getenv("AZURE_OPENAI_API_KEY"),
        os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        os.getenv("CHROMA_PATH"),
    )


def get_embedding_provider() -> EmbeddingProvider:
    """Return configured embedding provider instance.

    Precedence: Azure OpenAI -> Ollama (local) -> hash fallback.
    """
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    if azure_endpoint and azure_key and azure_deployment:
        return AzureOpenAIEmbeddingProvider(
            endpoint=azure_endpoint,
            api_key=azure_key,
            deployment=azure_deployment,
        )

    if os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_EMBEDDING_MODEL"):
        return OllamaEmbeddingProvider()

    return HashEmbeddingProvider()


def get_vector_store(
    embedding_provider: EmbeddingProvider | None = None,
) -> BaseVectorStore:
    """Return configured vector store instance.

    Precedence: Azure AI Search -> ChromaDB (persistent local) -> InMemory.
    Chroma replaces the in-memory store as the local default so indexed
    papers survive server restarts.
    """
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
        store = ChromaVectorStore(embedding_provider=provider)

    _VECTOR_STORE_CACHE[cache_key] = store
    return store


def get_discovery_vector_store(
    embedding_provider: EmbeddingProvider | None = None,
) -> BaseVectorStore:
    """Vector store for SemanticRetriever's OpenAlex abstract index.

    Uses its own Chroma collection so discovery's clear-and-reindex cycle
    never wipes the library evidence collection that /papers/upload fills.
    Azure Search keeps a single shared index (it filters by metadata instead).
    """
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_API_KEY")
    search_index = os.getenv("AZURE_SEARCH_INDEX")

    provider = embedding_provider or get_embedding_provider()

    if search_endpoint and search_key and search_index:
        return get_vector_store(embedding_provider=provider)

    return ChromaVectorStore(
        collection_name=DISCOVERY_COLLECTION,
        embedding_provider=provider,
    )


def get_retriever(use_semantic: bool = True) -> Retriever:
    """
    Factory function providing a configured Retriever instance.
    Defaults to SemanticRetriever using the dedicated discovery vector store.
    """
    if not use_semantic:
        return OpenAlexRetriever()

    provider = get_embedding_provider()
    store = get_discovery_vector_store(embedding_provider=provider)

    return SemanticRetriever(
        embedding_provider=provider,
        vector_store=store,
    )
