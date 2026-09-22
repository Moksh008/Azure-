import os
from typing import Optional

from app.embeddings.provider import EmbeddingProvider, HashEmbeddingProvider
from app.retrieval.evidence import EvidenceChunk
from app.retrieval.vector_store import BaseVectorStore

# Default collection names. The library store holds full-text chunks from
# uploaded/fetched papers; the discovery store holds OpenAlex abstracts.
# Keeping them separate is what allows SemanticRetriever to clear and
# rebuild its abstract index without ever wiping indexed library evidence.
LIBRARY_COLLECTION = "library_evidence"
DISCOVERY_COLLECTION = "openalex_abstracts"


def _clean_metadata(chunk: EvidenceChunk) -> dict:
    """Flatten a chunk's citation metadata for Chroma storage.

    Chroma rejects None metadata values, so optional fields are coerced to
    empty strings (or 0 for the page number).
    """
    return {
        "paper_id": chunk.paper_id,
        "title": chunk.title,
        "section": chunk.section or "",
        "page_number": chunk.page_number or 0,
        "source_url": chunk.source_url or "",
    }


class ChromaVectorStore(BaseVectorStore):
    """
    Local persistent vector store backed by ChromaDB. Chunks are upserted
    with their full citation metadata (paper_id, title, section,
    page_number, source_url) so every retrieval result stays grounded to
    paper + section + page. Data survives server restarts.
    """

    def __init__(
        self,
        path: Optional[str] = None,
        collection_name: str = LIBRARY_COLLECTION,
        embedding_provider: Optional[EmbeddingProvider] = None,
        get_client=None,
    ):
        self.path = path or os.getenv("CHROMA_PATH", "./chroma_db")
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        self._get_client = get_client  # test seam; defaults to chromadb.PersistentClient
        self._client = None
        self._collection = None

    def _ensure_collection(self):
        """Lazily create the persistent client and collection (cosine space)."""
        if self._collection is not None:
            return self._collection
        if self._get_client is not None:
            client = self._get_client()
        else:
            import chromadb

            try:
                from chromadb.config import Settings

                client = chromadb.PersistentClient(
                    path=self.path,
                    settings=Settings(anonymized_telemetry=False),
                )
            except ImportError:  # pragma: no cover - very old chromadb
                client = chromadb.PersistentClient(path=self.path)
        self._client = client
        self._collection = client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    def add_chunks(
        self,
        chunks: list[EvidenceChunk],
        vectors: list[list[float]] | None = None,
    ) -> None:
        if not chunks:
            return

        if vectors is None:
            vectors = self.embedding_provider.embed_batch([c.text for c in chunks])
        if len(vectors) != len(chunks):
            raise ValueError(
                f"Got {len(vectors)} vectors for {len(chunks)} chunks; counts must match."
            )

        collection = self._ensure_collection()
        collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=vectors,
            documents=[c.text for c in chunks],
            metadatas=[_clean_metadata(c) for c in chunks],
        )

    def search(self, query: str, top_k: int = 5) -> list[EvidenceChunk]:
        if not query or not query.strip():
            return []

        collection = self._ensure_collection()
        if collection.count() == 0:
            return []

        query_vector = self.embedding_provider.embed(query)
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=max(1, min(top_k, collection.count())),
            include=["documents", "metadatas"],
        )

        records = results["ids"][0]
        chunks: list[EvidenceChunk] = []
        for i, record_id in enumerate(records):
            metadata = results["metadatas"][0][i]
            chunks.append(
                EvidenceChunk(
                    chunk_id=record_id,
                    paper_id=metadata.get("paper_id", ""),
                    title=metadata.get("title", "Untitled"),
                    text=results["documents"][0][i] or "",
                    source_url=metadata.get("source_url") or None,
                    page_number=metadata.get("page_number") or None,
                    section=metadata.get("section") or None,
                )
            )
        return chunks

    def clear(self) -> None:
        # Drop and recreate the collection — version-proof (works whether or
        # not this chromadb build supports empty include lists) and cheap.
        self._ensure_collection()
        self._client.delete_collection(self.collection_name)
        self._collection = None
        self._ensure_collection()

    def __len__(self) -> int:
        return self._ensure_collection().count()
