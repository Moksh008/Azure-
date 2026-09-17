from backend.app.agents.analyzer import PaperAnalyzer
from backend.app.agents.qa import GroundedQA
from app.retrieval.factory import get_retriever
from backend.app.services.llm_service import LLMService
from shared.schemas import (
    EvidenceChunk,
    GroundedAnswer,
    PaperAnalysis,
)


class ResearchService:
    """Coordinate M2 retrieval with M3 analysis and Q&A."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def answer_question(
        self,
        question: str,
        top_k: int = 5,
    ) -> GroundedAnswer:
        if not question.strip():
            raise ValueError("Question cannot be empty")

        retriever = get_retriever()
        chunks = await retriever.retrieve(
            question=question,
            top_k=top_k,
        )
        evidence = [self._to_schema_chunk(chunk) for chunk in chunks]

        return GroundedQA(self.llm_service).answer(
            question=question,
            evidence=evidence,
        )

    async def analyze_paper(
        self,
        paper_id: str,
        paper_title: str,
        query: str,
        top_k: int = 5,
    ) -> PaperAnalysis:
        if not query.strip():
            raise ValueError("Analysis query cannot be empty")

        retriever = get_retriever()
        chunks = await retriever.retrieve(
            question=query,
            top_k=top_k,
        )
        evidence = [self._to_schema_chunk(chunk) for chunk in chunks]

        return PaperAnalyzer(self.llm_service).analyze(
            paper_id=paper_id,
            paper_title=paper_title,
            evidence=evidence,
        )

    @staticmethod
    def _to_schema_chunk(chunk) -> EvidenceChunk:
        return EvidenceChunk(
            chunk_id=chunk.chunk_id,
            paper_id=chunk.paper_id,
            paper_title=chunk.title,
            section=chunk.section,
            page=chunk.page_number,
            text=chunk.text,
        )
