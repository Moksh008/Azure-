from app.discovery.openalex_client import OpenAlexClient
from app.embeddings.provider import EmbeddingProvider, HashEmbeddingProvider
from app.retrieval.chunker import chunk_text
from app.retrieval.evidence import EvidenceChunk
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore


class SemanticRetriever(Retriever):
    """
    Semantic Retriever combining OpenAlex discovery, text chunking,
    embedding generation, and vector similarity search.
    """

    def __init__(
        self,
        openalex_client: OpenAlexClient | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: BaseVectorStore | None = None,
    ):
        self.client = openalex_client or OpenAlexClient()
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        # Discovery gets its own store (a dedicated Chroma collection locally)
        # because retrieve() clears it every call — sharing the library store
        # would wipe full-text evidence indexed from uploaded papers. Imported
        # here rather than at module level: factory imports this module.
        from app.retrieval.factory import get_discovery_vector_store

        self.vector_store = vector_store or get_discovery_vector_store(
            embedding_provider=self.embedding_provider
        )

    async def retrieve(
        self,
        question: str,
        top_k: int = 5,
        fetch_paper_count: int = 15,
    ) -> list[EvidenceChunk]:
        """
        1. Fetch candidate papers matching question/topic from OpenAlex.
        2. Chunk paper abstracts into EvidenceChunk objects preserving metadata.
        3. Index chunks into vector store with embeddings.
        4. Perform cosine-similarity vector search to return true top_k EvidenceChunks.
        """
        if not question or not question.strip():
            return []

        papers = self.client.search_papers(
            question,
            max_results=fetch_paper_count,
        )

        all_chunks: list[EvidenceChunk] = []
        seen_chunk_ids: set[str] = set()

        for paper in papers:
            if not paper or not paper.abstract or not paper.abstract.strip():
                continue

            text_chunks = chunk_text(
                paper.abstract,
                max_words=100,
                overlap_words=20,
            )

            for chunk_index, text in enumerate(text_chunks):
                cid = f"{paper.paper_id or 'paper'}-chunk-{chunk_index}"
                if cid in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(cid)

                all_chunks.append(
                    EvidenceChunk(
                        chunk_id=cid,
                        paper_id=paper.paper_id or "",
                        title=paper.title or "Untitled paper",
                        text=text,
                        source_url=paper.url or paper.doi,
                        section="Abstract",
                    )
                )

        if not all_chunks:
            return []

        self.vector_store.clear()
        self.vector_store.add_chunks(all_chunks)

        return self.vector_store.search(question, top_k=top_k)
