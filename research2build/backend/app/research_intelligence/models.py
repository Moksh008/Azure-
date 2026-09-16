"""M4-owned Pydantic models for Research Intelligence outputs.

These models define M4's output contracts only.
The upstream PaperAnalysis schema is owned by M2/M3 and will be
integrated once their contract is finalised.
"""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Paper Comparison
# ---------------------------------------------------------------------------

class PaperComparison(BaseModel):
    """Result of comparing multiple paper analyses.

    Captures shared themes, methodological overlaps, contradictions,
    and a list of common limitations surfaced across the compared papers.
    """

    comparison_id: str = Field(default_factory=lambda: uuid4().hex)
    paper_ids: list[str] = Field(
        default_factory=list,
        description="IDs of the papers that were compared.",
    )
    shared_themes: list[str] = Field(
        default_factory=list,
        description="Themes or topics that appear across multiple papers.",
    )
    methodological_overlaps: list[str] = Field(
        default_factory=list,
        description="Shared methodological approaches across the papers.",
    )
    contradictions: list[str] = Field(
        default_factory=list,
        description="Contradictory findings or claims between papers.",
    )
    common_limitations: list[str] = Field(
        default_factory=list,
        description="Limitations mentioned in more than one paper.",
    )


# ---------------------------------------------------------------------------
# Recurring Limitation
# ---------------------------------------------------------------------------

class RecurringLimitation(BaseModel):
    """A limitation that appears across multiple papers.

    Tracks which papers mention it and how frequently it recurs.
    """

    limitation_id: str = Field(default_factory=lambda: uuid4().hex)
    description: str = Field(
        ...,
        description="Human-readable description of the recurring limitation.",
    )
    paper_ids: list[str] = Field(
        default_factory=list,
        description="IDs of papers where this limitation was observed.",
    )
    frequency: int = Field(
        default=0,
        ge=0,
        description="Number of papers in which this limitation recurs.",
    )
    severity: str = Field(
        default="unknown",
        description="Estimated severity: low | medium | high | unknown.",
    )


# ---------------------------------------------------------------------------
# Research Opportunity
# ---------------------------------------------------------------------------

class ResearchOpportunity(BaseModel):
    """A *potential* research opportunity derived from recurring limitations.

    Important: the system does NOT claim verified novelty.
    `novelty_confidence` defaults to a disclaimer requiring human review.
    """

    opportunity_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str = Field(
        ...,
        description="Short title for the potential research opportunity.",
    )
    description: str = Field(
        ...,
        description="Explanation of why this may be a worthwhile direction.",
    )
    source_limitation_ids: list[str] = Field(
        default_factory=list,
        description="IDs of RecurringLimitations that motivated this opportunity.",
    )
    novelty_confidence: str = Field(
        default="Requires human validation",
        description=(
            "Confidence statement about novelty. "
            "The system never claims verified novelty; human review is required."
        ),
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Relevant keywords for discoverability.",
    )


# ---------------------------------------------------------------------------
# Project Proposal
# ---------------------------------------------------------------------------

class ProjectProposal(BaseModel):
    """A buildable project proposal generated from a research opportunity."""

    proposal_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str = Field(
        ...,
        description="Concise project title.",
    )
    summary: str = Field(
        ...,
        description="High-level summary of the proposed project.",
    )
    source_opportunity_ids: list[str] = Field(
        default_factory=list,
        description="IDs of ResearchOpportunities that inspired this proposal.",
    )
    objectives: list[str] = Field(
        default_factory=list,
        description="Key objectives the project aims to achieve.",
    )
    proposed_methods: list[str] = Field(
        default_factory=list,
        description="Suggested methods or approaches.",
    )
    expected_outcomes: list[str] = Field(
        default_factory=list,
        description="Anticipated deliverables or results.",
    )
    feasibility_notes: str = Field(
        default="",
        description="Preliminary notes on feasibility and resource requirements.",
    )
