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
