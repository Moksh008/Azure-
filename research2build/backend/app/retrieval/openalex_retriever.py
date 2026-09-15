from app.discovery.openalex_client import (
    format_paper_metadata,
    search_papers,
)
from app.retrieval.chunker import chunk_text
from app.retrieval.evidence import EvidenceChunk
from app.retrieval.retriever import Retriever


class OpenAlexRetriever(Retriever):
    async def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        papers = await search_papers(
            question,
            per_page=top_k,
        )

        chunks = []

        for paper in papers:
            metadata = format_paper_metadata(paper)

            if not metadata.abstract:
                continue

            text_chunks = chunk_text(
                metadata.abstract,
                max_words=100,
                overlap_words=20,
            )

            for chunk_index, text in enumerate(text_chunks):
                chunks.append(
                    EvidenceChunk(
                        chunk_id=(
                            f"{metadata.paper_id or 'paper'}"
                            f"-chunk-{chunk_index}"
                        ),
                        paper_id=metadata.paper_id or "",
                        title=metadata.title or "Untitled paper",
                        text=text,
                        source_url=metadata.source_url or metadata.doi,
                        section="Abstract",
                    )
                )

        return chunks[:top_k]
