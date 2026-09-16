"""M4 — Research Intelligence orchestration service.

Provides a single entry-point that chains the full M4 pipeline:

    papers (from M2/M3)
        → comparison
        → recurring limitations
        → potential research opportunities
        → buildable project proposals

The M2/M3 boundary is isolated: upstream data enters only through
``run_pipeline(papers)``.  Replacing ``Any`` with the real
PaperAnalysis type is the only change needed when their contract lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.research_intelligence.comparison import compare_papers
from backend.app.research_intelligence.limitations import (
    find_recurring_limitations,
)
from backend.app.research_intelligence.models import (
    PaperComparison,
    ProjectProposal,
    RecurringLimitation,
    ResearchOpportunity,
)
from backend.app.research_intelligence.opportunities import (
    generate_opportunities,
)
from backend.app.research_intelligence.project_generator import (
    generate_project_proposals,
)


# ---------------------------------------------------------------------------
# Pipeline result container
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """Holds every intermediate and final output of the M4 pipeline."""

    comparison: PaperComparison | None = None
    recurring_limitations: list[RecurringLimitation] = field(
        default_factory=list,
    )
    opportunities: list[ResearchOpportunity] = field(default_factory=list)
    proposals: list[ProjectProposal] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_pipeline(papers: list[Any]) -> PipelineResult:
    """Execute the full M4 Research Intelligence pipeline.

    Parameters
    ----------
    papers:
        A list of paper-analysis objects provided by M2/M3.
        Replace ``Any`` with the concrete type once their schema is final.

    Returns
    -------
    PipelineResult
        Contains the comparison, recurring limitations, opportunities,
        and project proposals generated during the run.
    """

    comparison = compare_papers(papers)
    limitations = find_recurring_limitations(papers)
    opportunities = generate_opportunities(limitations)
    proposals = generate_project_proposals(opportunities)

    return PipelineResult(
        comparison=comparison,
        recurring_limitations=limitations,
        opportunities=opportunities,
        proposals=proposals,
    )
