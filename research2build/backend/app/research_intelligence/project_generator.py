"""M4 — Project-proposal generation.

Converts a list of potential research opportunities into 3–5 buildable
project proposals.  No LLM integration is wired up yet; this module
provides the structural interface only.
"""

from __future__ import annotations

from backend.app.research_intelligence.models import (
    ProjectProposal,
    ResearchOpportunity,
)

# Desired range of proposals to generate.
MIN_PROPOSALS = 3
MAX_PROPOSALS = 5


def generate_project_proposals(
    opportunities: list[ResearchOpportunity],
) -> list[ProjectProposal]:
    """Generate buildable project proposals from research opportunities.

    Parameters
    ----------
    opportunities:
        Potential research opportunities identified by M4.

    Returns
    -------
    list[ProjectProposal]
        Between ``MIN_PROPOSALS`` and ``MAX_PROPOSALS`` actionable project
        proposals.  Each proposal references the opportunities it was
        derived from.
    """

    # -----------------------------------------------------------------
    # TODO(M4): Implement proposal generation.  Steps will include:
    #   1. Rank / prioritise opportunities by impact and feasibility.
    #   2. For each selected opportunity (or cluster), draft a proposal
    #      with objectives, methods, and expected outcomes.
    #   3. Add preliminary feasibility notes.
    #   4. Clamp output to MIN_PROPOSALS–MAX_PROPOSALS range.
    # -----------------------------------------------------------------

    return []
