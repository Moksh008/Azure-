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
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_API_KEY")
    search_index = os.getenv("AZURE_SEARCH_INDEX")

    provider = embedding_provider or get_embedding_provider()

    if search_endpoint and search_key and search_index:
        return AzureAISearchVectorStore(
            endpoint=search_endpoint,
            api_key=search_key,
            index_name=search_index,
            embedding_provider=provider,
        )

    return InMemoryVectorStore(embedding_provider=provider)


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
