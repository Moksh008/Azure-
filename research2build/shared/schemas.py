from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class EvidenceChunk(BaseModel):
    chunk_id: str
    paper_id: str
    paper_title: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    text: str


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
