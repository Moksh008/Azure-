import os
from typing import Optional

import httpx

from app.embeddings.provider import EmbeddingProvider, HashEmbeddingProvider
from app.retrieval.evidence import EvidenceChunk
from app.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore


class AzureAISearchVectorStore(BaseVectorStore):
    """
    Production vector store implementation using Azure AI Search.
    Communicates via Azure Search REST API with vector search capabilities.
    Falls back to InMemoryVectorStore if RETRIEVAL_ALLOW_LOCAL_FALLBACK is enabled.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        api_version: str = "2023-11-01",
        allow_fallback: Optional[bool] = None,
    ):
        self.endpoint = endpoint.rstrip("/") if endpoint else None
        self.api_key = api_key
        self.index_name = index_name
        self.api_version = api_version
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()

        if allow_fallback is None:
            allow_fallback = (
                os.getenv("RETRIEVAL_ALLOW_LOCAL_FALLBACK", "true").lower()
                == "true"
            )
        self.allow_fallback = allow_fallback
        self._fallback_store = InMemoryVectorStore(
            embedding_provider=self.embedding_provider
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key and self.index_name)

    def get_index_schema(self, vector_dim: int = 128) -> dict:
        """Return the JSON index schema definition for Azure AI Search vector index."""
        return {
            "name": self.index_name or "research2build-evidence",
            "fields": [
                {
                    "name": "chunk_id",
                    "type": "Edm.String",
                    "key": True,
                    "searchable": False,
                },
                {
                    "name": "original_chunk_id",
                    "type": "Edm.String",
                    "searchable": False,
                },
                {
                    "name": "paper_id",
                    "type": "Edm.String",
                    "searchable": True,
                    "filterable": True,
                },
                {"name": "title", "type": "Edm.String", "searchable": True},
                {"name": "text", "type": "Edm.String", "searchable": True},
                {
                    "name": "source_url",
                    "type": "Edm.String",
                    "searchable": False,
                },
                {
                    "name": "page_number",
                    "type": "Edm.Int32",
                    "filterable": True,
                },
                {"name": "section", "type": "Edm.String", "searchable": True},
                {
                    "name": "vector",
                    "type": "Collection(Edm.Single)",
                    "searchable": True,
                    "dimensions": vector_dim,
                    "vectorSearchProfile": "hnsw-profile",
                },
            ],
            "vectorSearch": {
                "algorithms": [{"name": "hnsw-config", "kind": "hnsw"}],
                "profiles": [
                    {
                        "name": "hnsw-profile",
                        "algorithm": "hnsw-config",
                    }
                ],
            },
        }

    def ensure_index_exists(self) -> bool:
        """Create or validate the search index on Azure AI Search."""
        if not self.is_configured:
            if not self.allow_fallback:
                raise RuntimeError(
                    "Azure AI Search unconfigured and local fallback disabled."
                )
            return False

        url = f"{self.endpoint}/indexes('{self.index_name}')?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    return True

                schema = self.get_index_schema()
                create_url = f"{self.endpoint}/indexes?api-version={self.api_version}"
                create_res = client.post(
                    create_url, json=schema, headers=headers
                )
                create_res.raise_for_status()
                return True
        except Exception as err:
            if not self.allow_fallback:
                raise RuntimeError(
                    f"Azure AI Search index initialization failed: {err}"
                ) from err
            return False

    def add_chunks(
        self,
        chunks: list[EvidenceChunk],
        vectors: list[list[float]] | None = None,
    ) -> None:
        if not chunks:
            return

        if not self.is_configured:
            if not self.allow_fallback:
                raise RuntimeError(
                    "Azure AI Search credentials missing and local fallback disabled."
                )
            self._fallback_store.add_chunks(chunks, vectors)
            return

        if vectors is None:
            texts = [c.text for c in chunks]
            vectors = self.embedding_provider.embed_batch(texts)

        documents = []
        for chunk, vector in zip(chunks, vectors):
            safe_id = (
                chunk.chunk_id.replace(":", "_")
                .replace("/", "_")
                .replace(".", "_")
            )
            doc = {
                "@search.action": "mergeOrUpload",
                "chunk_id": safe_id,
                "original_chunk_id": chunk.chunk_id,
                "paper_id": chunk.paper_id or "",
                "title": chunk.title or "",
                "text": chunk.text or "",
                "source_url": chunk.source_url or "",
                "page_number": chunk.page_number
                if chunk.page_number is not None
                else 0,
                "section": chunk.section or "",
                "vector": vector,
            }
            documents.append(doc)

        url = f"{self.endpoint}/indexes('{self.index_name}')/docs/index?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    url, json={"value": documents}, headers=headers
                )
                res.raise_for_status()
        except Exception as err:
            if not self.allow_fallback:
                raise RuntimeError(
                    f"Azure AI Search document upload failed: {err}"
                ) from err
            self._fallback_store.add_chunks(chunks, vectors)

    def search(self, query: str, top_k: int = 5) -> list[EvidenceChunk]:
        if not query or not query.strip():
            return []

        if not self.is_configured:
            if not self.allow_fallback:
                raise RuntimeError(
                    "Azure AI Search credentials missing and local fallback disabled."
                )
            return self._fallback_store.search(query, top_k=top_k)

        query_vector = self.embedding_provider.embed(query)
        return self.search_by_vector(
            query_vector, top_k=top_k, query_text=query
        )

    def search_by_vector(
        self,
        query_vector: list[float],
        top_k: int = 5,
        query_text: str = "*",
    ) -> list[EvidenceChunk]:
        if not self.is_configured:
            if not self.allow_fallback:
                raise RuntimeError(
                    "Azure AI Search credentials missing and local fallback disabled."
                )
            return self._fallback_store.search_by_vector(
                query_vector, top_k=top_k
            )

        url = f"{self.endpoint}/indexes('{self.index_name}')/docs/search?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "search": query_text if query_text else "*",
            "top": top_k,
            "vectorQueries": [
                {
                    "kind": "vector",
                    "vector": query_vector,
                    "fields": "vector",
                    "k": top_k,
                }
            ],
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            results = []
            for doc in data.get("value", []):
                chunk_id = doc.get("original_chunk_id") or doc.get(
                    "chunk_id", ""
                )
                page_num = doc.get("page_number")
                if page_num == 0:
                    page_num = None

                results.append(
                    EvidenceChunk(
                        chunk_id=chunk_id,
                        paper_id=doc.get("paper_id", ""),
                        title=doc.get("title", ""),
                        text=doc.get("text", ""),
                        source_url=doc.get("source_url") or None,
                        page_number=page_num,
                        section=doc.get("section") or None,
                    )
                )
            return results
        except Exception as err:
            if not self.allow_fallback:
                raise RuntimeError(
                    f"Azure AI Search vector query failed: {err}"
                ) from err
            return self._fallback_store.search_by_vector(
                query_vector, top_k=top_k
            )

    def clear(self) -> None:
        self._fallback_store.clear()
