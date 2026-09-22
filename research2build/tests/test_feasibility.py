"""Tests for Member 5 — Feasibility Engine & Roadmap Generator."""

import pytest
from pydantic import ValidationError

from backend.app.agents.feasibility import (
    FeasibilityConstraints,
    Roadmap,
    generate_roadmap,
    score_feasibility,
)
from backend.app.research_intelligence.models import ProjectProposal


def _proposal(**overrides) -> ProjectProposal:
    defaults = dict(
        title="Model Compression Toolkit",
        summary="Quantize and prune models to cut GPU memory usage.",
        objectives=["Quantize weights", "Profile memory", "Deploy compressed model"],
        key_features=["Quantization profiler", "Latency dashboard"],
        technical_approach=["Python", "PyTorch", "BitsAndBytes", "ONNX Runtime"],
        proposed_methods=["BitsAndBytes quantization", "Structured pruning"],
    )
    defaults.update(overrides)
    return ProjectProposal(**defaults)


class TestFeasibilityConstraints:
    def test_requires_team_size_and_weeks(self):
        with pytest.raises(ValidationError):
            FeasibilityConstraints()

    def test_defaults(self):
        c = FeasibilityConstraints(team_size=2, weeks_available=8)
        assert c.budget_usd == 0.0
        assert c.skills == []


class TestScoreFeasibility:
    def test_well_matched_team_scores_high(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(
            team_size=3,
            weeks_available=10,
            budget_usd=100,
            skills=["Python", "PyTorch", "BitsAndBytes", "ONNX Runtime"],
        )
        result = score_feasibility(proposal, constraints)
        assert result.level in {"high", "medium"}
        assert result.skill_coverage == 1.0
        assert result.risks == []

    def test_components_breakdown_present_and_bounded(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(
            team_size=3,
            weeks_available=10,
            budget_usd=100,
            skills=["Python", "PyTorch", "BitsAndBytes", "ONNX Runtime"],
        )
        result = score_feasibility(proposal, constraints)

        labels = {c.label for c in result.components}
        assert labels == {
            "Implementation Time",
            "Team Skill Fit",
            "Budget / Hardware Fit",
            "Technical Complexity",
        }
        for component in result.components:
            assert 0 <= component.score <= 100
            assert component.explanation

        skill_component = next(c for c in result.components if c.label == "Team Skill Fit")
        assert skill_component.score == 100  # full skill coverage in this fixture

    def test_mismatched_team_scores_low_with_risks(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(
            team_size=1,
            weeks_available=1,
            budget_usd=0,
            skills=["HTML"],
        )
        result = score_feasibility(proposal, constraints)
        assert result.level in {"low", "not_feasible"}
        assert result.risks  # at least one risk surfaced
        assert any("effort" in r.lower() for r in result.risks)

    def test_gpu_heavy_zero_budget_flags_constraint_note(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(team_size=2, weeks_available=8, budget_usd=0)
        result = score_feasibility(proposal, constraints)
        assert any("budget" in n.lower() for n in result.constraint_notes)

    def test_score_bounds_and_proposal_id_traced(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(team_size=2, weeks_available=8)
        result = score_feasibility(proposal, constraints)
        assert 0 <= result.score <= 100
        assert result.proposal_id == proposal.proposal_id

    def test_roadmap_never_exceeds_available_weeks(self):
        proposal = _proposal(objectives=["a", "b", "c", "d", "e", "f"])
        constraints = FeasibilityConstraints(team_size=1, weeks_available=4)
        result = score_feasibility(proposal, constraints)
        assert result.roadmap.total_weeks <= 4.0 + 1e-6


class TestGenerateRoadmap:
    def test_seven_phases_in_order(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(team_size=2, weeks_available=14)
        roadmap = generate_roadmap(proposal, constraints)
        assert isinstance(roadmap, Roadmap)
        phases = [m.phase for m in roadmap.milestones]
        assert phases == [
            "Research", "Dataset", "Backend", "AI",
            "Frontend", "Testing", "Deployment",
        ]

    def test_milestones_are_contiguous(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(team_size=2, weeks_available=14)
        roadmap = generate_roadmap(proposal, constraints)
        for prev, nxt in zip(roadmap.milestones, roadmap.milestones[1:]):
            assert prev.end_week == nxt.start_week

    def test_ai_milestone_includes_proposed_methods(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(team_size=2, weeks_available=14)
        roadmap = generate_roadmap(proposal, constraints)
        ai_milestone = next(m for m in roadmap.milestones if m.phase == "AI")
        assert "BitsAndBytes quantization" in ai_milestone.deliverables

    def test_handles_empty_key_features_and_methods(self):
        proposal = _proposal(key_features=[], proposed_methods=[])
        constraints = FeasibilityConstraints(team_size=1, weeks_available=6)
        roadmap = generate_roadmap(proposal, constraints)
        assert roadmap.total_weeks > 0
        assert all(m.duration_weeks >= 0 for m in roadmap.milestones)
