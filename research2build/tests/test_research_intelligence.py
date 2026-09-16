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

        with pytest.raises(ValueError, match="At least two"):
            compare_papers(None)

    def test_returns_paper_comparison(self):
        result = compare_papers(["a", "b"])
        assert isinstance(result, PaperComparison)
        assert result.paper_ids == ["a", "b"]

    def test_comparison_of_two_valid_papers(self):
        p1 = {
            "id": "p1",
            "title": "Efficient RAG with LoRA",
            "abstract": "We study retrieval augmented generation using transformer models and LoRA.",
            "research_question": "Can LoRA improve retrieval augmented generation efficiency?",
            "methodology": ["LoRA fine-tuning", "Vector index retrieval"],
            "datasets": ["SQuAD 2.0", "HotpotQA"],
            "key_findings": ["Accuracy improved on complex questions."],
            "limitations": ["High latency during peak load."],
        }
        p2 = {
            "id": "p2",
            "title": "Scalable RAG using Prompt Tuning",
            "abstract": "Evaluating retrieval augmented generation with transformer architectures.",
            "research_question": "How does prompt tuning scale in retrieval augmented generation?",
            "methodology": ["Prompt tuning", "Vector index retrieval"],
            "datasets": ["SQuAD 2.0", "TriviaQA"],
            "key_findings": ["Latency decreased with prompt cache."],
            "limitations": ["High latency during cold starts."],
        }
        result = compare_papers([p1, p2])
        assert isinstance(result, PaperComparison)
        assert result.paper_ids == ["p1", "p2"]
        assert len(result.shared_themes) > 0
        assert any("RAG" in theme or "Retrieval" in theme for theme in result.shared_themes)
        assert "SQuAD 2.0" in result.shared_datasets
        assert any("TriviaQA" in diff for diff in result.dataset_differences)
        assert any("HotpotQA" in diff for diff in result.dataset_differences)
        assert len(result.key_findings) == 2
        assert len(result.all_limitations) == 2

    def test_comparison_of_three_papers(self):
        papers = [
            {
                "id": "p1",
                "title": "Survey on NLP Transformers",
                "methodology": ["Transformer architecture", "Self-attention"],
                "datasets": ["GLUE"],
                "limitations": ["High computational cost"],
            },
            {
                "id": "p2",
                "title": "Optimizing NLP Transformers",
                "methodology": ["Transformer architecture", "Quantization"],
                "datasets": ["GLUE", "SuperGLUE"],
                "limitations": ["High computational cost"],
            },
            {
                "id": "p3",
                "title": "Distilling NLP Transformers",
                "methodology": ["Transformer architecture", "Knowledge distillation"],
                "datasets": ["GLUE", "SQuAD"],
                "limitations": ["High computational cost"],
            },
        ]
        result = compare_papers(papers)
        assert len(result.paper_ids) == 3
        assert result.paper_ids == ["p1", "p2", "p3"]
        assert "Transformer architecture" in result.methodological_overlaps
        assert "GLUE" in result.shared_datasets
        assert "High computational cost" in result.common_limitations

    def test_dictionary_input(self):
        p1 = {"title": "Doc A", "methodology": ["Method 1"], "datasets": ["Data X"]}
        p2 = {"title": "Doc B", "methodology": ["Method 1"], "datasets": ["Data Y"]}
        result = compare_papers([p1, p2])
        assert result.paper_ids == ["Doc A", "Doc B"]
        assert "Method 1" in result.methodological_overlaps

    def test_pydantic_object_input(self):
        from pydantic import BaseModel as BM

        class SamplePaper(BM):
            paper_id: str
            title: str
            methodology: list[str]
            datasets: list[str]
            limitations: list[str] = []

        p1 = SamplePaper(
            paper_id="sp1",
            title="Paper One",
            methodology=["LoRA"],
            datasets=["Dataset A"],
            limitations=["Limited hardware"],
        )
        p2 = SamplePaper(
            paper_id="sp2",
            title="Paper Two",
            methodology=["LoRA", "Pruning"],
            datasets=["Dataset A", "Dataset B"],
            limitations=["Limited hardware"],
        )
        result = compare_papers([p1, p2])
        assert result.paper_ids == ["sp1", "sp2"]
        assert "LoRA" in result.methodological_overlaps
        assert "Dataset A" in result.shared_datasets
        assert "Limited hardware" in result.common_limitations

    def test_missing_optional_fields(self):
        # Empty dicts or minimal dicts
        p1 = {"id": "doc1"}
        p2 = {}
        result = compare_papers([p1, p2])
        assert result.paper_ids == ["doc1", "paper_2"]
        assert result.shared_themes == []
        assert result.methodological_overlaps == []
        assert result.shared_datasets == []
        assert result.key_findings == []

    def test_common_theme_detection(self):
        p1 = {
            "id": "p1",
            "title": "Deep Neural Networks for Medical Imaging",
            "abstract": "We analyze deep neural networks applied to medical imaging classification.",
        }
        p2 = {
            "id": "p2",
            "title": "Advances in Deep Neural Networks for Radiology",
            "abstract": "We investigate deep neural networks in radiology and medical imaging tasks.",
        }
        result = compare_papers([p1, p2])
        assert len(result.shared_themes) > 0
        # Stop words should NOT be present as themes
        forbidden_themes = {"the", "and", "we", "for", "in", "paper", "study", "approach"}
        for theme in result.shared_themes:
            assert theme.lower() not in forbidden_themes

    def test_methodology_comparison(self):
        p1 = {
            "id": "m1",
            "methodology": ["Supervised Fine-Tuning", "Reinforcement Learning"],
        }
        p2 = {
            "id": "m2",
            "methodology": ["Supervised Fine-Tuning", "Direct Preference Optimization"],
        }
        result = compare_papers([p1, p2])
        assert "Supervised Fine-Tuning" in result.methodological_overlaps
        assert any("Reinforcement Learning" in d for d in result.methodological_differences)
        assert any("Direct Preference Optimization" in d for d in result.methodological_differences)

    def test_dataset_comparison(self):
        p1 = {
            "id": "d1",
            "datasets": ["ImageNet-1k", "COCO"],
        }
        p2 = {
            "id": "d2",
            "datasets": ["ImageNet-1k", "Pascal VOC"],
        }
        result = compare_papers([p1, p2])
        assert "ImageNet-1k" in result.shared_datasets
        assert any("COCO" in d for d in result.dataset_differences)
        assert any("Pascal VOC" in d for d in result.dataset_differences)

    def test_limitations_preservation(self):
        p1 = {
            "id": "l1",
            "limitations": ["Small sample size", "Evaluation compute overhead"],
        }
        p2 = {
            "id": "l2",
            "limitations": ["Small sample size", "Lack of demographic diversity"],
        }
        result = compare_papers([p1, p2])
        # Preserves all limitations
        assert len(result.all_limitations) == 4
        assert any("[l1] Small sample size" in lim for lim in result.all_limitations)
        assert any("[l2] Small sample size" in lim for lim in result.all_limitations)
        # Identifies common limitation
        assert "Small sample size" in result.common_limitations
        # Must NOT claim research gap
        for lim in result.common_limitations:
            assert "research gap" not in lim.lower()
            assert "novelty" not in lim.lower()

    def test_deterministic_output(self):
        p1 = {
            "id": "p1",
            "title": "Study A",
            "methodology": ["Method X", "Method Y"],
            "datasets": ["Dataset 1"],
            "key_findings": ["Finding Alpha"],
            "limitations": ["Limitation A"],
        }
        p2 = {
            "id": "p2",
            "title": "Study B",
            "methodology": ["Method X", "Method Z"],
            "datasets": ["Dataset 1", "Dataset 2"],
            "key_findings": ["Finding Beta"],
            "limitations": ["Limitation A", "Limitation B"],
        }
        run1 = compare_papers([p1, p2])
        run2 = compare_papers([p1, p2])

        assert run1.paper_ids == run2.paper_ids
        assert run1.shared_themes == run2.shared_themes
        assert run1.methodological_overlaps == run2.methodological_overlaps
        assert run1.methodological_differences == run2.methodological_differences
        assert run1.shared_datasets == run2.shared_datasets
        assert run1.dataset_differences == run2.dataset_differences
        assert run1.key_findings == run2.key_findings
        assert run1.common_limitations == run2.common_limitations
        assert run1.all_limitations == run2.all_limitations
        assert run1.agreements == run2.agreements
        assert run1.differences == run2.differences
        assert run1.contradictions == run2.contradictions

    def test_contradiction_detection(self):
        p1 = {
            "id": "p1",
            "key_findings": ["Model accuracy improved under high noise conditions."],
        }
        p2 = {
            "id": "p2",
            "key_findings": ["Model accuracy degraded under high noise conditions."],
        }
        result = compare_papers([p1, p2])
        assert len(result.contradictions) > 0
        assert "accuracy" in result.contradictions[0].lower()

    def test_agreements_and_differences(self):
        p1 = {
            "id": "p1",
            "title": "Quantum ML for Chemistry",
            "methodology": ["Variational Quantum Eigensolver"],
            "datasets": ["QM9"],
        }
        p2 = {
            "id": "p2",
            "title": "Quantum ML for Physics",
            "methodology": ["Quantum Approximate Optimization Algorithm"],
            "datasets": ["QM9"],
        }
        result = compare_papers([p1, p2])
        # Agreement on dataset QM9
        assert any("QM9" in a for a in result.agreements)
        # Difference in methodology
        assert any("Variational Quantum Eigensolver" in d for d in result.differences)
        assert any("Quantum Approximate Optimization Algorithm" in d for d in result.differences)


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
