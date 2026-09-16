from app.discovery.openalex_client import OpenAlexClient
from app.retrieval.chunker import chunk_text
from app.retrieval.evidence import EvidenceChunk
from app.retrieval.retriever import Retriever


class OpenAlexRetriever(Retriever):
    async def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[EvidenceChunk]:
        client = OpenAlexClient()
        papers = client.search_papers(
            question,
            max_results=top_k,
        )

        chunks = []

        for paper in papers:
            if not paper.abstract:
                continue

            text_chunks = chunk_text(
                paper.abstract,
                max_words=100,
                overlap_words=20,
            )

            for chunk_index, text in enumerate(text_chunks):
                chunks.append(
                    EvidenceChunk(
                        chunk_id=f"{paper.paper_id or 'paper'}-chunk-{chunk_index}",
                        paper_id=paper.paper_id or "",
                        title=paper.title or "Untitled paper",
                        text=text,
                        source_url=paper.url or paper.doi,
                        section="Abstract",
                    )
                )

        return chunks[:top_k]
