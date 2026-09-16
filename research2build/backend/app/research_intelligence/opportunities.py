"""M4 — Research-opportunity generation.

Transforms a list of recurring limitations into *potential* research
opportunities.  The system does NOT claim verified novelty — every
generated opportunity defaults to ``novelty_confidence = "Requires
human validation"``.
"""

from __future__ import annotations

from backend.app.research_intelligence.models import (
    RecurringLimitation,
    ResearchOpportunity,
)


def generate_opportunities(
    recurring_limitations: list[RecurringLimitation],
) -> list[ResearchOpportunity]:
    """Generate potential research opportunities from recurring limitations.

    Parameters
    ----------
    recurring_limitations:
        Limitations that appeared across multiple paper analyses.

    Returns
    -------
    list[ResearchOpportunity]
        Potential research directions.  Each opportunity carries a
        ``novelty_confidence`` disclaimer requiring human review.
    """

    # -----------------------------------------------------------------
    # TODO(M4): Implement opportunity generation.  Steps will include:
    #   1. Group related limitations by topic / domain.
    #   2. For each group, formulate a potential research direction.
    #   3. Link back to source limitation IDs.
    #   4. Assign keywords for discoverability.
    #   5. Keep novelty_confidence = "Requires human validation".
    # -----------------------------------------------------------------

    return []
