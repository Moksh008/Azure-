"""Tests for Member 5 — Deliverables Engine (PRD + MVP scaffold)."""

from pathlib import Path

import pytest

from backend.app.agents.deliverables import (
    generate_mvp_scaffold,
    generate_prd,
    write_scaffold,
)
from backend.app.agents.feasibility import FeasibilityConstraints, score_feasibility
from backend.app.research_intelligence.models import ProjectProposal, ResearchOpportunity


def _proposal(**overrides) -> ProjectProposal:
    defaults = dict(
        title="Model Compression Toolkit",
        summary="Quantize and prune models to cut GPU memory usage.",
        problem_statement="Large models are too expensive to run on consumer hardware.",
        objectives=["Quantize weights", "Profile memory", "Deploy compressed model"],
        key_features=["Quantization profiler", "Latency dashboard"],
        technical_approach=["Python", "PyTorch", "BitsAndBytes", "ONNX Runtime"],
        proposed_methods=["BitsAndBytes quantization", "Structured pruning"],
        expected_outcomes=["Reproducible compression pipeline", "Benchmark report"],
        evidence=["Paper 2 reports OOM errors on consumer GPUs."],
        source_opportunity_ids=["opp_1"],
    )
    defaults.update(overrides)
    return ProjectProposal(**defaults)


class TestGeneratePRD:
    def test_basic_fields_populated(self):
        proposal = _proposal()
        prd = generate_prd(proposal)
        assert prd.proposal_id == proposal.proposal_id
        assert prd.title == proposal.title
        assert prd.problem_statement == proposal.problem_statement
        assert prd.evidence == proposal.evidence
        assert prd.novelty_confidence == "Requires human validation"

    def test_markdown_contains_all_sections_and_disclaimer(self):
        proposal = _proposal()
        prd = generate_prd(proposal)
        md = prd.to_markdown()
        for heading in [
            "## Problem", "## Evidence", "## Potential Opportunity",
            "## Solution", "## Expected Contribution", "## Feasibility", "## Roadmap",
        ]:
            assert heading in md
        assert "Requires human validation" in md
        assert "does not claim to have" in md

    def test_opportunity_summary_uses_opportunity_when_given(self):
        proposal = _proposal()
        opp = ResearchOpportunity(
            opportunity_id="opp_1",
            title="Compression research gap",
            description="Consumer GPUs run out of memory on large models.",
        )
        prd = generate_prd(proposal, opportunity=opp)
        assert "Consumer GPUs run out of memory" in prd.opportunity_summary
        assert "inferred from recurring limitations" in prd.opportunity_summary

    def test_feasibility_summary_uses_assessment_when_given(self):
        proposal = _proposal()
        constraints = FeasibilityConstraints(team_size=2, weeks_available=8, skills=["Python"])
        assessment = score_feasibility(proposal, constraints)
        prd = generate_prd(proposal, feasibility=assessment)
        assert str(assessment.score) in prd.feasibility_summary
        assert len(prd.roadmap_summary) == len(assessment.roadmap.milestones)

    def test_falls_back_gracefully_with_no_opportunity_or_feasibility(self):
        proposal = _proposal(feasibility_notes="Looks doable with 2 people.")
        prd = generate_prd(proposal)
        assert "Looks doable" in prd.feasibility_summary
        assert prd.roadmap_summary == []


class TestGenerateMvpScaffold:
    def test_contains_expected_files(self):
        proposal = _proposal()
        manifest = generate_mvp_scaffold(proposal)
        for path in [
            "README.md", "requirements.txt", ".gitignore",
            "backend/requirements.txt", "backend/.env.example", "backend/app/main.py",
            "frontend/package.json", "frontend/.env.example", "frontend/README.md",
        ]:
            assert path in manifest

    def test_readme_reflects_proposal_content(self):
        proposal = _proposal()
        manifest = generate_mvp_scaffold(proposal)
        assert proposal.title in manifest["README.md"]
        assert "Quantize weights" in manifest["README.md"]
        assert "starter scaffold, not a finished implementation" in manifest["README.md"]

    def test_main_py_is_valid_python_and_not_a_fake_full_app(self):
        proposal = _proposal()
        manifest = generate_mvp_scaffold(proposal)
        source = manifest["backend/app/main.py"]
        compile(source, "main.py", "exec")  # syntax must be valid
        assert "TODO" in source

    def test_handles_empty_proposal_fields(self):
        proposal = _proposal(objectives=[], key_features=[], technical_approach=[])
        manifest = generate_mvp_scaffold(proposal)
        assert "TODO: define objectives" in manifest["README.md"]
        assert "TODO: define key features" in manifest["README.md"]


class TestWriteScaffold:
    def test_writes_all_files_to_disk(self, tmp_path: Path):
        proposal = _proposal()
        manifest = generate_mvp_scaffold(proposal)
        written = write_scaffold(manifest, tmp_path)
        assert len(written) == len(manifest)
        for rel_path in manifest:
            assert (tmp_path / rel_path).exists()
            assert (tmp_path / rel_path).read_text(encoding="utf-8") == manifest[rel_path]

    def test_rejects_path_escaping_output_dir(self, tmp_path: Path):
        manifest = {"../escape.txt": "malicious"}
        with pytest.raises(ValueError):
            write_scaffold(manifest, tmp_path)
