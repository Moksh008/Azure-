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
from shared.schemas import PaperAnalysis


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
