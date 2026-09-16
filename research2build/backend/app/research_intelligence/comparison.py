"""M4 — Paper comparison service.

Accepts a collection of paper-analysis objects from M2/M3 and produces
a PaperComparison summarising shared themes, methodological overlaps,
contradictions, and common limitations.

The upstream PaperAnalysis schema is NOT defined here.  The function
signature uses `list[Any]` as a placeholder until the M2/M3 contract
is finalised, at which point `Any` should be replaced with the
concrete PaperAnalysis type.
"""

from __future__ import annotations

from typing import Any

from backend.app.research_intelligence.models import PaperComparison


def compare_papers(papers: list[Any]) -> PaperComparison:
    """Compare a collection of paper analyses and return a PaperComparison.

    Parameters
    ----------
    papers:
        A list of paper-analysis objects whose schema is owned by M2/M3.
        Once their contract is available, replace ``Any`` with the real type.

    Returns
    -------
    PaperComparison
        A structured comparison result.

    Raises
    ------
    ValueError
        If fewer than two papers are provided (comparison is meaningless).
    """

    if len(papers) < 2:
        raise ValueError(
            "At least two paper analyses are required for comparison."
        )

    # -----------------------------------------------------------------
    # TODO(M4): Implement comparison logic once M2/M3 PaperAnalysis
    #           schema is available.  Steps will include:
    #   1. Extract themes / topics from each paper analysis.
    #   2. Identify methodological overlaps.
    #   3. Detect contradictions between findings.
    #   4. Collect limitations shared across papers.
    # -----------------------------------------------------------------

    return PaperComparison(
        paper_ids=[],  # populate from papers once schema is known
    )
