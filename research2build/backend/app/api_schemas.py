"""Request/response models for the integration routes in main.py.

These glue together the M1-M4 modules (discovery, comparison, opportunity
generation, project generation) plus Member 5's feasibility/deliverables
engines. Kept separate from research_intelligence/models.py, which is M4's
own output contract — these are just the HTTP envelopes around calling it.

All of these stay stateless by design: the caller passes the objects it
already has (e.g. the PaperAnalysis results from prior /analysis calls)
rather than IDs the server would need a database to resolve. That matches
the existing comparison/limitations/opportunities/project_generator
modules, which all operate on in-memory objects with no persistence layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.agents.feasibility import FeasibilityAssessment, FeasibilityConstraints
from backend.app.research_intelligence.models import ProjectProposal, ResearchOpportunity
from shared.schemas import EvidenceChunk, GroundedAnswer, PaperAnalysis


class DiscoveryRequest(BaseModel):
    query: str
    max_results: int = Field(default=20, ge=1, le=100)


class DiscoveredPaper(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    abstract: str | None = None
    url: str | None = None
    pdf_url: str | None = None  # direct OA PDF link, when OpenAlex has one


class FetchFullTextRequest(BaseModel):
    paper_id: str
    title: str
    pdf_url: str


class CompareRequest(BaseModel):
    analyses: list[PaperAnalysis] = Field(min_length=2)


class OpportunitiesRequest(BaseModel):
    analyses: list[PaperAnalysis] = Field(min_length=1)


class ProposalsRequest(BaseModel):
    opportunities: list[ResearchOpportunity] = Field(min_length=1)


class FeasibilityRequest(BaseModel):
    proposal: ProjectProposal
    constraints: FeasibilityConstraints


class PRDRequest(BaseModel):
    proposal: ProjectProposal
    opportunity: ResearchOpportunity | None = None
    feasibility: FeasibilityAssessment | None = None


# -- unified chat workflow ---------------------------------------------------
#
# Stateless like everything else here: the frontend is the source of truth
# for the paper library and selection, and sends the relevant slice on every
# call. `library` is metadata-only (cheap to send/route on); `evidence` is
# scoped to whatever the caller currently has selected.


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class LibraryPaperRef(BaseModel):
    paper_id: str
    title: str
    source: str  # "upload" | "discovery"


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)
    library: list[LibraryPaperRef] = Field(default_factory=list)
    evidence: list[EvidenceChunk] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    action: str  # "search" | "analyze" | "ask" | "chat"
    discovered_papers: list[DiscoveredPaper] | None = None
    analyses: list[PaperAnalysis] | None = None  # "analyze" — one or more papers
    answer: GroundedAnswer | None = None
