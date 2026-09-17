"""Shared data contracts for Research2Build.

CONTRACT FREEZE (v1.0) — EvidenceChunk and Citation
----------------------------------------------------
These models are the stable interface between ingestion (M1),
retrieval/embeddings (M2), and analysis/Q&A/RAG (M3).

Every generated claim must be grounded in evidence from a paper.
"""

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0"


class HealthResponse(BaseModel):
    status: str
    service: str


class EvidenceChunk(BaseModel):
    """One retrievable unit of paper text."""

    chunk_id: str
    paper_id: str
    paper_title: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    text: str


class Citation(BaseModel):
    """Grounding evidence attached to one generated claim.

    A citation is created from an EvidenceChunk and contains the
    specific excerpt that supports the generated claim.
    """

    chunk_id: str
    paper_id: str
    paper_title: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    quote: str

    @classmethod
    def from_chunk(
        cls,
        chunk: EvidenceChunk,
        quote: str | None = None,
    ) -> "Citation":
        """Build a Citation from an EvidenceChunk.

        If no quote is supplied, the complete chunk text is used.
        """

        return cls(
            chunk_id=chunk.chunk_id,
            paper_id=chunk.paper_id,
            paper_title=chunk.paper_title,
            section=chunk.section,
            page=chunk.page,
            quote=quote if quote is not None else chunk.text,
        )


class GroundedClaim(BaseModel):
    """An LLM-generated claim paired with supporting citations.

    Every generated claim must have at least one citation.
    """

    claim: str
    citations: list[Citation] = Field(min_length=1)

    @property
    def text(self) -> str:
        return self.claim


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievalResult(BaseModel):
    chunks: list[EvidenceChunk]


class AnalysisRequest(BaseModel):
    paper_id: str
    paper_title: str
    evidence: list[EvidenceChunk]


class QARequest(BaseModel):
    question: str
    evidence: list[EvidenceChunk]


class RetrievedQARequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)


class PaperAnalysis(BaseModel):
    """Structured, evidence-grounded analysis of one research paper."""

    paper_id: str
    paper_title: str

    problem: GroundedClaim | None = None
    objective: GroundedClaim | None = None
    methodology: GroundedClaim | None = None
    dataset: GroundedClaim | None = None
    models: GroundedClaim | None = None

    results: list[GroundedClaim] = Field(default_factory=list)
    limitations: list[GroundedClaim] = Field(default_factory=list)
    future_work: list[GroundedClaim] = Field(default_factory=list)


class GroundedAnswer(BaseModel):
    """Answer to a research question with supporting citations."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    evidence_sufficient: bool = True