from abc import ABC, abstractmethod
import math
from typing import Sequence

from app.embeddings.provider import EmbeddingProvider, HashEmbeddingProvider
from app.retrieval.evidence import EvidenceChunk


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    if len(vec_a) != len(vec_b) or not vec_a or not vec_b:
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


class BaseVectorStore(ABC):
    """
    Abstract vector store interface for both local (InMemoryVectorStore)
    and cloud persistent (AzureAISearchVectorStore) backends.
    """

    @abstractmethod
    def add_chunks(
        self,
        chunks: list[EvidenceChunk],
        vectors: list[list[float]] | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[EvidenceChunk]:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    """
    In-memory vector store for EvidenceChunks.
    Supports indexing chunks with vector embeddings and performing top-k similarity search.
    """

    def __init__(self, embedding_provider: EmbeddingProvider | None = None):
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        self._records: list[dict] = []

    def add_chunks(
        self,
        chunks: list[EvidenceChunk],
        vectors: list[list[float]] | None = None,
    ) -> None:
        if not chunks:
            return

        if vectors is None:
            texts = [c.text for c in chunks]
            vectors = self.embedding_provider.embed_batch(texts)

        for chunk, vector in zip(chunks, vectors):
            self._records.append({"chunk": chunk, "vector": vector})

    def search(self, query: str, top_k: int = 5) -> list[EvidenceChunk]:
        if not query or not query.strip():
            return []

        query_vector = self.embedding_provider.embed(query)
        return self.search_by_vector(query_vector, top_k=top_k)

    def search_by_vector(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        if not self._records or not query_vector:
            return []

        scored_records = []
        for record in self._records:
            score = cosine_similarity(query_vector, record["vector"])
            scored_records.append((score, record["chunk"]))

        scored_records.sort(key=lambda item: item[0], reverse=True)

        return [chunk for _, chunk in scored_records[:top_k]]

    def clear(self) -> None:
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)
