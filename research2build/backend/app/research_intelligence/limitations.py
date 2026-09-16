"""M4 — Recurring-limitations extraction.

Scans a collection of paper analyses to identify limitations that recur
across multiple papers.

The upstream PaperAnalysis schema is NOT defined here.  ``Any`` is used
as a placeholder until the M2/M3 contract is finalised.
"""

from __future__ import annotations

from typing import Any

from backend.app.research_intelligence.models import RecurringLimitation


def find_recurring_limitations(papers: list[Any]) -> list[RecurringLimitation]:
    """Identify limitations that appear across multiple papers.

    Parameters
    ----------
    papers:
        A list of paper-analysis objects whose schema is owned by M2/M3.

    Returns
    -------
    list[RecurringLimitation]
        Limitations observed in more than one paper, ranked by frequency.
    """

    # -----------------------------------------------------------------
    # TODO(M4): Implement limitation extraction once M2/M3 PaperAnalysis
    #           schema is available.  Steps will include:
    #   1. Extract the limitations section from each paper analysis.
    #   2. Normalise / cluster similar limitation descriptions.
    #   3. Count cross-paper frequency and assign severity.
    #   4. Return only limitations appearing in ≥ 2 papers.
    # -----------------------------------------------------------------

    return []
