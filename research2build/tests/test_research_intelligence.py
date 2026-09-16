"""Tests for M4 — Research Intelligence module.

These tests validate the M4 output models, interface contracts, and
the service orchestration layer independently of M2/M3 data.
"""

import pytest
from pydantic import ValidationError

from backend.app.research_intelligence.models import (
    PaperComparison,
    ProjectProposal,
    RecurringLimitation,
    ResearchOpportunity,
)
from backend.app.research_intelligence.comparison import compare_papers
from backend.app.research_intelligence.limitations import (
    find_recurring_limitations,
)
from backend.app.research_intelligence.opportunities import (
    generate_opportunities,
)
from backend.app.research_intelligence.project_generator import (
    generate_project_proposals,
)
from backend.app.research_intelligence.service import run_pipeline, PipelineResult


# ── Model tests ─────────────────────────────────────────────────────

class TestPaperComparison:
    def test_defaults(self):
        pc = PaperComparison()
        assert pc.comparison_id  # auto-generated
        assert pc.paper_ids == []
        assert pc.shared_themes == []
        assert pc.methodological_overlaps == []
        assert pc.contradictions == []
        assert pc.common_limitations == []

    def test_custom_values(self):
        pc = PaperComparison(
            paper_ids=["p1", "p2"],
            shared_themes=["NLP"],
            common_limitations=["small dataset"],
        )
        assert pc.paper_ids == ["p1", "p2"]
        assert pc.shared_themes == ["NLP"]
        assert pc.common_limitations == ["small dataset"]


class TestRecurringLimitation:
    def test_requires_description(self):
        with pytest.raises(ValidationError):
            RecurringLimitation()  # description is required

    def test_defaults(self):
        rl = RecurringLimitation(description="Limited sample size")
        assert rl.limitation_id
        assert rl.frequency == 0
        assert rl.severity == "unknown"
        assert rl.paper_ids == []

    def test_frequency_non_negative(self):
        with pytest.raises(ValidationError):
            RecurringLimitation(description="x", frequency=-1)


class TestResearchOpportunity:
    def test_requires_title_and_description(self):
        with pytest.raises(ValidationError):
            ResearchOpportunity()

    def test_novelty_confidence_default(self):
        ro = ResearchOpportunity(
            title="Explore X",
            description="Recurring limitation Y suggests potential direction.",
        )
        assert ro.novelty_confidence == "Requires human validation"

    def test_keywords_default(self):
        ro = ResearchOpportunity(title="T", description="D")
        assert ro.keywords == []


class TestProjectProposal:
    def test_requires_title_and_summary(self):
        with pytest.raises(ValidationError):
            ProjectProposal()

    def test_defaults(self):
        pp = ProjectProposal(title="Build X", summary="A project to build X.")
        assert pp.proposal_id
        assert pp.objectives == []
        assert pp.proposed_methods == []
        assert pp.expected_outcomes == []
        assert pp.feasibility_notes == ""


# ── Interface contract tests ────────────────────────────────────────

class TestComparison:
    def test_requires_at_least_two_papers(self):
        with pytest.raises(ValueError, match="At least two"):
            compare_papers([])

        with pytest.raises(ValueError, match="At least two"):
            compare_papers(["only_one"])

    def test_returns_paper_comparison(self):
        result = compare_papers(["a", "b"])
        assert isinstance(result, PaperComparison)


class TestLimitations:
    def test_returns_list(self):
        result = find_recurring_limitations([])
        assert isinstance(result, list)


class TestOpportunities:
    def test_returns_list(self):
        result = generate_opportunities([])
        assert isinstance(result, list)


class TestProjectGenerator:
    def test_returns_list(self):
        result = generate_project_proposals([])
        assert isinstance(result, list)


# ── Service / pipeline tests ────────────────────────────────────────

class TestPipeline:
    def test_pipeline_returns_result(self):
        result = run_pipeline(["paper_a", "paper_b"])
        assert isinstance(result, PipelineResult)
        assert isinstance(result.comparison, PaperComparison)
        assert isinstance(result.recurring_limitations, list)
        assert isinstance(result.opportunities, list)
        assert isinstance(result.proposals, list)

    def test_pipeline_rejects_single_paper(self):
        with pytest.raises(ValueError):
            run_pipeline(["only_one"])
