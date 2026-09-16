"""Shared data contracts for Research2Build.

CONTRACT FREEZE (v1.0) — EvidenceChunk and Citation
----------------------------------------------------
These two models are the stable interface between ingestion (M1),
retrieval/embeddings (M2), and analysis/Q&A/RAG (M3). Their fields are
frozen for v1: additive/optional fields may be proposed via PR, but no
existing field may be renamed, retyped, or removed without agreement
across all three owners (see research2build/ARCHITECTURE.md).

- EvidenceChunk is what ingestion produces per paper and what retrieval
  indexes/returns from a similarity search.
- Citation is what any LLM-generated claim must carry as its grounding —
  built from one EvidenceChunk plus the specific quoted excerpt that
  supports the claim (see CLAUDE.md: "no ungrounded claim without a
  citation").
"""

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class HealthResponse(BaseModel):
    status: str
    service: str


class EvidenceChunk(BaseModel):
    """One retrievable unit of paper text, produced by ingestion (M1).

    Field semantics:
    - chunk_id: unique within a paper; format `{paper_id}-{0001...}`. Stable
      across re-ingestion only if the source PDF and chunking config are
      unchanged — do not assume permanence across pipeline versions.
    - paper_id: unique per ingested paper (12-char hex from ingestion).
    - paper_title: human-readable title, for display and citation text.
    - section: canonical section name (e.g. "Introduction", "Limitations")
      if detected, else None. None means "unknown section", not "no section".
    - page: 1-indexed page number the chunk starts on, if known.
    - text: normalized chunk text (whitespace/hyphenation cleaned). This is
      the unit M2 embeds and indexes, and the unit M3 retrieves and quotes
      from.
    """

    chunk_id: str
    paper_id: str
    paper_title: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    text: str


class Citation(BaseModel):
    """Grounding evidence attached to one LLM-generated claim (M3 output).

    Every function that returns a generated claim (Q&A answer, analysis
    field, opportunity, project) must return one Citation per supporting
    chunk alongside it. `quote` should be a short excerpt of `EvidenceChunk
    .text` (not the full chunk) — the smallest span that actually supports
    the claim, so a reader can verify it without opening the source chunk.
    """

    chunk_id: str
    paper_id: str
    paper_title: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    quote: str

    @classmethod
    def from_chunk(cls, chunk: EvidenceChunk, quote: str | None = None) -> "Citation":
        """Build a Citation from the EvidenceChunk it grounds.

        `quote` defaults to the full chunk text; callers should pass the
        specific excerpt that supports their claim when one is available.
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
    """An LLM-generated claim paired with the Citations that support it.

    Any function returning generated text downstream of retrieval (Q&A
    answers, analysis fields, opportunities, projects) should return
    GroundedClaims rather than bare strings, so grounding can't be
    silently dropped. `citations` must be non-empty: a claim with no
    supporting evidence violates the project's core rule that no
    ungrounded claim may be produced (see CLAUDE.md).
    """

    claim: str
    citations: list[Citation] = Field(min_length=1)


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievalResult(BaseModel):
    chunks: list[EvidenceChunk]

class Citation(BaseModel):
    chunk_id: str
    paper_id: str
    paper_title: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)


class GroundedClaim(BaseModel):
    text: str
    citations: list[Citation] = Field(default_factory=list)


class PaperAnalysis(BaseModel):
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
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    evidence_sufficient: bool = True
