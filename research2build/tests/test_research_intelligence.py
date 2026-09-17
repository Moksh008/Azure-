"""Tests for M4 — Research Intelligence module.

These tests validate the M4 output models, interface contracts, and
the service orchestration layer independently of M2/M3 data.
"""

from typing import Any

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

    def test_none_input(self):
        result = find_recurring_limitations(None)
        assert result == []

    def test_two_papers_with_same_limitation(self):
        p1 = {"id": "p1", "limitations": ["High GPU memory consumption"]}
        p2 = {"id": "p2", "limitations": ["High GPU memory consumption"]}
        result = find_recurring_limitations([p1, p2])

        assert len(result) == 1
        assert isinstance(result[0], RecurringLimitation)
        assert result[0].frequency == 2
        assert result[0].paper_ids == ["p1", "p2"]

    def test_three_papers_with_recurring_limitation(self):
        papers = [
            {"id": "p1", "limitations": ["Inference latency is high during burst queries."]},
            {"id": "p2", "limitations": ["Slow inference latency observed under load."]},
            {"id": "p3", "limitations": ["High inference latency remains a major bottleneck."]},
        ]
        result = find_recurring_limitations(papers)

        assert len(result) == 1
        assert result[0].frequency == 3
        assert result[0].paper_ids == ["p1", "p2", "p3"]
        assert result[0].severity == "high"

    def test_differently_worded_conceptually_similar_limitations(self):
        papers = [
            {"id": "p1", "limitations": ["limited training data"]},
            {"id": "p2", "limitations": ["small dataset size"]},
            {"id": "p3", "limitations": ["insufficient data for training"]},
        ]
        result = find_recurring_limitations(papers)

        assert len(result) == 1
        assert result[0].frequency == 3
        assert result[0].paper_ids == ["p1", "p2", "p3"]
        assert "data" in result[0].description.lower() or "dataset" in result[0].description.lower()

    def test_unrelated_limitations_sharing_one_word_not_merged(self):
        # Should NOT merge merely because both use 'limited'
        papers = [
            {"id": "p1", "limitations": ["limited model interpretability"]},
            {"id": "p2", "limitations": ["limited training data"]},
        ]
        result = find_recurring_limitations(papers)
        # Neither recurs in >= 2 papers, so result must be empty
        assert result == []

    def test_unique_limitation_single_paper(self):
        papers = [
            {"id": "p1", "limitations": ["Specialized microphone hardware required"]},
            {"id": "p2", "limitations": ["Only tested on English text"]},
        ]
        result = find_recurring_limitations(papers)
        assert result == []

    def test_papers_with_no_limitations(self):
        papers = [
            {"id": "p1", "title": "Paper One", "limitations": []},
            {"id": "p2", "title": "Paper Two"},
            {"id": "p3", "title": "Paper Three", "limitations": None},
        ]
        result = find_recurring_limitations(papers)
        assert result == []

    def test_dictionary_input(self):
        papers = [
            {"paper_id": "doc1", "weaknesses": ["Scalability bottlenecks on large graphs"]},
            {"paper_id": "doc2", "challenges": ["Fails to scale on large graphs"]},
        ]
        result = find_recurring_limitations(papers)
        assert len(result) == 1
        assert result[0].paper_ids == ["doc1", "doc2"]
        assert result[0].frequency == 2

    def test_pydantic_object_input(self):
        from pydantic import BaseModel as BM

        class PaperModel(BM):
            paper_id: str
            title: str
            limitations: list[str]

        p1 = PaperModel(paper_id="m1", title="M1", limitations=["High annotation cost for human labels"])
        p2 = PaperModel(paper_id="m2", title="M2", limitations=["Expensive human labeling and annotation"])

        result = find_recurring_limitations([p1, p2])
        assert len(result) == 1
        assert result[0].paper_ids == ["m1", "m2"]
        assert result[0].frequency == 2

    def test_multiple_different_recurring_limitations(self):
        papers = [
            {
                "id": "p1",
                "limitations": [
                    "High computational cost and GPU memory demand",
                    "High inference latency under load",
                ],
            },
            {
                "id": "p2",
                "limitations": [
                    "High compute overhead requiring expensive hardware",
                    "High inference latency during peak hours",
                ],
            },
            {
                "id": "p3",
                "limitations": [
                    "High computational cost with multi-GPU requirement",
                ],
            },
        ]
        result = find_recurring_limitations(papers)
        assert len(result) == 2
        # First should be compute cost (freq 3), second should be latency (freq 2)
        assert result[0].frequency == 3
        assert result[1].frequency == 2

    def test_preservation_of_original_limitation_evidence(self):
        papers = [
            {"id": "p1", "limitations": ["Limited training data available for rare disease classes."]},
            {"id": "p2", "limitations": ["Small dataset size restricts broader clinical adoption."]},
        ]
        result = find_recurring_limitations(papers)
        assert len(result) == 1
        assert hasattr(result[0], "evidence")
        assert len(result[0].evidence) == 2
        assert any("[p1] Limited training data" in ev for ev in result[0].evidence)
        assert any("[p2] Small dataset size" in ev for ev in result[0].evidence)

    def test_deterministic_output(self):
        papers = [
            {"id": "p1", "limitations": ["High compute cost", "Limited data"]},
            {"id": "p2", "limitations": ["High compute cost", "Limited data"]},
        ]
        run1 = find_recurring_limitations(papers)
        run2 = find_recurring_limitations(papers)

        assert len(run1) == len(run2)
        for r1, r2 in zip(run1, run2):
            assert r1.limitation_id == r2.limitation_id
            assert r1.description == r2.description
            assert r1.paper_ids == r2.paper_ids
            assert r1.frequency == r2.frequency
            assert r1.severity == r2.severity
            assert r1.evidence == r2.evidence

    def test_no_unsupported_research_gap_novelty_claims(self):
        papers = [
            {"id": "p1", "limitations": ["Lack of demographic diversity"]},
            {"id": "p2", "limitations": ["Dataset bias and demographic representation"]},
        ]
        result = find_recurring_limitations(papers)
        for rl in result:
            assert "research gap" not in rl.description.lower()
            assert "novelty" not in rl.description.lower()
            assert "gap" not in rl.description.lower()


class TestOpportunities:
    def test_returns_list(self):
        result = generate_opportunities([])
        assert isinstance(result, list)

    def test_empty_input(self):
        result = generate_opportunities([])
        assert result == []

    def test_none_input(self):
        result = generate_opportunities(None)
        assert result == []

    def test_one_recurring_limitation_to_one_opportunity(self):
        lim = RecurringLimitation(
            limitation_id="lim_1",
            description="Limited training data and small dataset size",
            paper_ids=["p1", "p2"],
            frequency=2,
            severity="medium",
            evidence=["[p1] limited data", "[p2] small dataset"],
        )
        opps = generate_opportunities([lim])
        assert len(opps) == 1
        opp = opps[0]
        assert isinstance(opp, ResearchOpportunity)
        assert opp.source_limitation_ids == ["lim_1"]
        assert "Data-Efficient" in opp.title
        assert len(opp.keywords) > 0

    def test_multiple_recurring_limitations(self):
        lim1 = RecurringLimitation(
            limitation_id="lim_1",
            description="High computational cost and hardware resource demands",
            paper_ids=["p1", "p2"],
            frequency=2,
        )
        lim2 = RecurringLimitation(
            limitation_id="lim_2",
            description="High inference latency and runtime overhead",
            paper_ids=["p1", "p3"],
            frequency=2,
        )
        opps = generate_opportunities([lim1, lim2])
        assert len(opps) == 2
        titles = {opp.title for opp in opps}
        assert "Model Compression and Compute-Efficient Optimization" in titles
        assert "Low-Latency Inference Acceleration and Caching" in titles

    def test_common_limitation_categories(self):
        categories = [
            ("Limited training data", "Data-Efficient Learning"),
            ("High computational cost and GPU memory overhead", "Model Compression"),
            ("High inference latency during peak queries", "Low-Latency Inference"),
            ("Scalability bottlenecks on large graphs", "Distributed Scaling"),
            ("Susceptibility to hallucinations and unfaithful answers", "Grounded Factuality"),
            ("Limited model interpretability", "Interpretable Architectures"),
            ("Dataset bias and lack of demographic diversity", "Balanced Benchmarking"),
            ("High manual annotation cost", "Active Learning"),
            ("Narrow evaluation on synthetic benchmarks", "Ecological Validity"),
            ("High sensitivity to prompts and noise", "Robust Optimization"),
        ]
        for desc, expected_title_part in categories:
            lim = RecurringLimitation(
                description=desc,
                paper_ids=["p1", "p2"],
                frequency=2,
            )
            opps = generate_opportunities([lim])
            assert len(opps) == 1, f"Failed for limitation: {desc}"
            assert expected_title_part in opps[0].title, f"Expected '{expected_title_part}' in '{opps[0].title}' for '{desc}'"

    def test_unknown_limitation_fallback(self):
        lim = RecurringLimitation(
            limitation_id="custom_1",
            description="Audio waveform distortion under reverberant room acoustics",
            paper_ids=["pA", "pB"],
            frequency=2,
            evidence=["[pA] audio distortion observed"],
        )
        opps = generate_opportunities([lim])
        assert len(opps) == 1
        opp = opps[0]
        assert "Audio Waveform Distortion" in opp.title
        assert "Audio waveform distortion under reverberant room acoustics" in opp.description
        assert opp.source_limitation_ids == ["custom_1"]

    def test_supporting_paper_ids_preserved(self):
        lim = RecurringLimitation(
            description="High computational cost",
            paper_ids=["paper_alpha", "paper_beta", "paper_gamma"],
            frequency=3,
        )
        opps = generate_opportunities([lim])
        assert len(opps) == 1
        assert opps[0].paper_ids == ["paper_alpha", "paper_beta", "paper_gamma"]

    def test_evidence_preserved(self):
        lim = RecurringLimitation(
            description="Limited training data",
            paper_ids=["p1", "p2"],
            evidence=["[p1] limited samples in rare classes", "[p2] few labeled records"],
        )
        opps = generate_opportunities([lim])
        assert len(opps) == 1
        assert len(opps[0].evidence) == 2
        assert "[p1] limited samples in rare classes" in opps[0].evidence
        assert "[p2] few labeled records" in opps[0].evidence

    def test_novelty_confidence_is_requires_human_validation(self):
        lim = RecurringLimitation(
            description="Scalability bottlenecks",
            paper_ids=["p1", "p2"],
        )
        opps = generate_opportunities([lim])
        assert len(opps) == 1
        assert opps[0].novelty_confidence == "Requires human validation"

    def test_no_research_gap_claim(self):
        lim = RecurringLimitation(
            description="High computational cost",
            paper_ids=["p1", "p2"],
        )
        opps = generate_opportunities([lim])
        for opp in opps:
            assert "research gap" not in opp.title.lower()
            assert "research gap" not in opp.description.lower()
            assert "novelty" not in opp.title.lower()

    def test_deterministic_output(self):
        lim1 = RecurringLimitation(
            limitation_id="l1",
            description="High compute overhead",
            paper_ids=["p1", "p2"],
        )
        lim2 = RecurringLimitation(
            limitation_id="l2",
            description="High inference latency",
            paper_ids=["p2", "p3"],
        )
        run1 = generate_opportunities([lim1, lim2])
        run2 = generate_opportunities([lim1, lim2])

        assert len(run1) == len(run2)
        for o1, o2 in zip(run1, run2):
            assert o1.opportunity_id == o2.opportunity_id
            assert o1.title == o2.title
            assert o1.description == o2.description
            assert o1.source_limitation_ids == o2.source_limitation_ids
            assert o1.novelty_confidence == o2.novelty_confidence
            assert o1.keywords == o2.keywords
            assert o1.paper_ids == o2.paper_ids
            assert o1.evidence == o2.evidence

    def test_duplicate_opportunity_prevention(self):
        # Two limitations that belong to the same core category
        lim1 = RecurringLimitation(
            limitation_id="lim_a",
            description="Limited training data",
            paper_ids=["p1", "p2"],
            evidence=["[p1] few examples"],
        )
        lim2 = RecurringLimitation(
            limitation_id="lim_b",
            description="Small dataset size",
            paper_ids=["p2", "p3"],
            evidence=["[p3] small dataset"],
        )
        opps = generate_opportunities([lim1, lim2])
        # Should be deduplicated into a single combined opportunity
        assert len(opps) == 1
        opp = opps[0]
        assert "Data-Efficient" in opp.title
        assert "lim_a" in opp.source_limitation_ids
        assert "lim_b" in opp.source_limitation_ids
        assert set(opp.paper_ids) == {"p1", "p2", "p3"}
        assert len(opp.evidence) == 2

    def test_malformed_entries_handled_safely(self):
        # Gracefully handle None and dict inputs
        inputs = [
            None,
            {"limitation_id": "dict_1", "description": "High latency", "paper_ids": ["d1", "d2"]},
            {"description": ""},
        ]
        opps = generate_opportunities(inputs)
        assert len(opps) == 1
        assert "Low-Latency" in opps[0].title


class TestProjectGenerator:
    def test_returns_list(self):
        result = generate_project_proposals([])
        assert isinstance(result, list)

    def test_empty_input(self):
        result = generate_project_proposals([])
        assert result == []

    def test_none_input(self):
        result = generate_project_proposals(None)
        assert result == []

    def test_one_valid_opportunity(self):
        opp = ResearchOpportunity(
            opportunity_id="opp_1",
            title="Data-Efficient Learning and Synthetic Augmentation",
            description="Investigate data-efficient learning methods to reduce labeled dataset dependence.",
            keywords=["data efficiency", "semi-supervised"],
            paper_ids=["p1", "p2"],
            evidence=["[p1] limited data"],
        )
        proposals = generate_project_proposals([opp])
        # 1 opportunity generates 3 distinct grounded directions
        assert len(proposals) == 3
        for p in proposals:
            assert isinstance(p, ProjectProposal)
            assert "opp_1" in p.source_opportunity_ids
            assert p.paper_ids == ["p1", "p2"]
            assert p.evidence == ["[p1] limited data"]
            assert p.novelty_confidence == "Requires human validation"

    def test_generation_of_three_to_five_proposals(self):
        opps_2 = [
            ResearchOpportunity(title="Data-Efficient Learning", description="Alleviate data scarcity"),
            ResearchOpportunity(title="Model Compression", description="Reduce GPU memory"),
        ]
        res_2 = generate_project_proposals(opps_2)
        assert 3 <= len(res_2) <= 5

        opps_4 = [
            ResearchOpportunity(title="Data-Efficient Learning", description="Alleviate data scarcity"),
            ResearchOpportunity(title="Model Compression", description="Reduce GPU memory"),
            ResearchOpportunity(title="Low-Latency Inference", description="Accelerate inference"),
            ResearchOpportunity(title="Grounded Factuality", description="Mitigate hallucinations"),
        ]
        res_4 = generate_project_proposals(opps_4)
        assert len(res_4) == 4

        opps_7 = [
            ResearchOpportunity(title=f"Opp {i}", description=f"Desc {i}") for i in range(7)
        ]
        res_7 = generate_project_proposals(opps_7)
        assert len(res_7) == 5  # Clamped to MAX_PROPOSALS

    def test_malformed_missing_fields(self):
        inputs = [
            None,
            {"title": ""},
            {"opportunity_id": "opp_dict", "title": "Low-Latency Inference", "description": "Reduce latency"},
        ]
        res = generate_project_proposals(inputs)
        assert len(res) == 3
        assert any("Low-Latency" in p.title for p in res)

    def test_major_opportunity_domains(self):
        domains = [
            ("Model Compression and Compute-Efficient Optimization", "Quantization Toolkit"),
            ("Low-Latency Inference Acceleration", "Speculative Decoding"),
            ("Distributed Scaling and Sub-Quadratic Architectures", "Scaling Benchmark"),
            ("Domain-Robust Representations", "Cross-Domain Robustness"),
            ("Grounded Factuality and Verification Mechanisms", "Factuality Verification"),
            ("Balanced Benchmarking and Algorithmic Debiasing", "Debiasing"),
            ("Interpretable Architectures and Mechanistic Explainability", "Interpretability"),
            ("Active Learning and Weak Supervision Pipelines", "Programmatic Labeling"),
            ("Ecological Validity and Real-World Evaluation Frameworks", "Stress-Testing"),
            ("Robust Optimization and Sensitivity Minimization", "Prompt Perturbation"),
        ]
        for opp_title, expected_keyword in domains:
            opp = ResearchOpportunity(title=opp_title, description=f"Address {opp_title}")
            props = generate_project_proposals([opp])
            assert len(props) >= 1
            assert any(expected_keyword.lower() in p.title.lower() for p in props), f"Failed for {opp_title}"

    def test_generic_fallback(self):
        opp = ResearchOpportunity(
            opportunity_id="custom_opp",
            title="Acoustic Waveform Restoration",
            description="Reconstruct corrupted audio signals in noisy acoustic environments.",
            keywords=["audio", "acoustics", "restoration"],
            paper_ids=["pA"],
            evidence=["[pA] audio corruption observed"],
        )
        props = generate_project_proposals([opp])
        assert len(props) == 3
        assert "Acoustic Waveform Restoration" in props[0].title
        assert "Acoustic Waveform Restoration" in props[1].title
        assert "custom_opp" in props[0].source_opportunity_ids
        assert props[0].paper_ids == ["pA"]

    def test_distinct_proposal_generation(self):
        opp = ResearchOpportunity(
            title="Data-Efficient Learning and Synthetic Augmentation",
            description="Investigate data efficiency",
        )
        props = generate_project_proposals([opp])
        titles = [p.title for p in props]
        assert len(set(titles)) == len(titles)  # All titles must be distinct
        summaries = [p.summary for p in props]
        assert len(set(summaries)) == len(summaries)  # All summaries must be distinct

    def test_duplicate_prevention(self):
        opp1 = ResearchOpportunity(opportunity_id="o1", title="Model Compression", description="Reduce GPU footprint")
        opp2 = ResearchOpportunity(opportunity_id="o2", title="Model Compression", description="Reduce GPU footprint")
        props = generate_project_proposals([opp1, opp2])
        titles = [p.title for p in props]
        assert len(set(titles)) == len(titles)

    def test_supporting_ids_and_evidence_preserved(self):
        opp = ResearchOpportunity(
            opportunity_id="opp_target",
            title="Grounded Factuality",
            description="Mitigate hallucinations",
            paper_ids=["paper_101", "paper_102"],
            evidence=["[paper_101] model hallucinated dates", "[paper_102] wrong facts"],
        )
        props = generate_project_proposals([opp])
        for p in props:
            assert p.source_opportunity_ids == ["opp_target"]
            assert p.paper_ids == ["paper_101", "paper_102"]
            assert "[paper_101] model hallucinated dates" in p.evidence
            assert "[paper_102] wrong facts" in p.evidence

    def test_novelty_confidence_is_requires_human_validation(self):
        opp = ResearchOpportunity(title="Data Efficiency", description="Data scarcity")
        props = generate_project_proposals([opp])
        for p in props:
            assert p.novelty_confidence == "Requires human validation"

    def test_deterministic_output(self):
        opp1 = ResearchOpportunity(opportunity_id="o1", title="Data Efficiency", description="Desc 1", paper_ids=["p1"])
        opp2 = ResearchOpportunity(opportunity_id="o2", title="Model Compression", description="Desc 2", paper_ids=["p2"])
        run1 = generate_project_proposals([opp1, opp2])
        run2 = generate_project_proposals([opp1, opp2])

        assert len(run1) == len(run2)
        for p1, p2 in zip(run1, run2):
            assert p1.proposal_id == p2.proposal_id
            assert p1.title == p2.title
            assert p1.summary == p2.summary
            assert p1.problem_statement == p2.problem_statement
            assert p1.source_opportunity_ids == p2.source_opportunity_ids
            assert p1.objectives == p2.objectives
            assert p1.proposed_methods == p2.proposed_methods
            assert p1.expected_outcomes == p2.expected_outcomes
            assert p1.key_features == p2.key_features
            assert p1.technical_approach == p2.technical_approach
            assert p1.feasibility_notes == p2.feasibility_notes
            assert p1.paper_ids == p2.paper_ids
            assert p1.evidence == p2.evidence
            assert p1.novelty_confidence == p2.novelty_confidence

    def test_no_research_gap_or_novelty_claims(self):
        opp = ResearchOpportunity(title="Model Compression", description="Reduce GPU memory")
        props = generate_project_proposals([opp])
        for p in props:
            assert "research gap" not in p.title.lower()
            assert "research gap" not in p.summary.lower()
            assert "research gap" not in p.problem_statement.lower()
            assert "novelty" not in p.title.lower()
            assert "novelty" not in p.summary.lower()

    def test_no_unrelated_fabricated_research_topics(self):
        opp = ResearchOpportunity(
            title="Data-Efficient Learning and Synthetic Augmentation",
            description="Investigate semi-supervised learning and synthetic data augmentation.",
        )
        props = generate_project_proposals([opp])
        for p in props:
            combined = f"{p.title} {p.summary} {p.problem_statement}".lower()
            # Must remain related to data/augmentation/samples
            assert any(term in combined for term in ["data", "synthetic", "sample", "supervis", "learning"])
            # Must NOT fabricate unrelated quantum or robotics topics
            assert "quantum" not in combined
            assert "robotics" not in combined


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

    def test_pipeline_with_recurring_limitations(self):
        papers = [
            {"id": "p1", "title": "Paper 1", "limitations": ["Small dataset size"]},
            {"id": "p2", "title": "Paper 2", "limitations": ["Limited training data"]},
        ]
        result = run_pipeline(papers)
        assert isinstance(result, PipelineResult)
        assert len(result.recurring_limitations) == 1
        assert result.recurring_limitations[0].frequency == 2
        assert len(result.opportunities) == 1
        assert "Data-Efficient" in result.opportunities[0].title
        assert len(result.proposals) >= 3
        assert any("Data-Efficient" in p.title for p in result.proposals)


# ── Full End-to-End Pipeline Tests ──────────────────────────────────

class TestEndToEndPipeline:
    """End-to-end test suite for the complete M4 Research Intelligence pipeline.

    Chains:
        PaperAnalysis-like inputs
            ↓ compare_papers()
            ↓ find_recurring_limitations()
            ↓ generate_opportunities()
            ↓ generate_project_proposals()
    """

    @pytest.fixture
    def realistic_rag_papers(self) -> list[dict[str, Any]]:
        """Realistic PaperAnalysis-like test fixtures from the RAG research domain."""
        return [
            {
                "paper_id": "paper_rag_dense",
                "title": "Dense Passage Retrieval for Real-Time Open-Domain Question Answering",
                "authors": ["K. Karpukhin", "B. Oguz", "S. Min"],
                "abstract": (
                    "We investigate dual-encoder dense retrieval architectures combined with "
                    "sequence-to-sequence readers for open-domain QA. Dense representations "
                    "outperform BM25 but suffer from substantial inference latency and memory overhead."
                ),
                "research_question": "Can dense passage embeddings replace sparse indexing while maintaining real-time latency?",
                "methodology": ["Dual-encoder dense retrieval", "FAISS vector indexing", "In-batch negative cross-entropy"],
                "datasets": ["Natural Questions", "TriviaQA", "MS-MARCO"],
                "key_findings": [
                    "Dense retrieval achieves 78.4% top-20 accuracy, exceeding BM25 by 9.2%.",
                    "Inference latency increases significantly when index size exceeds GPU VRAM.",
                ],
                "limitations": [
                    "High inference latency during peak traffic and multi-turn conversational queries.",
                    "Prohibitive GPU memory requirements for indexing large document corpora.",
                    "Susceptibility to hallucinations when retrieved passages contain conflicting facts.",
                ],
            },
            {
                "paper_id": "paper_rag_fusion",
                "title": "Fusion-in-Decoder: Leveraging Diverse Retrieved Contexts for Knowledge Grounding",
                "authors": ["G. Izacard", "E. Grave"],
                "abstract": (
                    "We propose Fusion-in-Decoder (FiD) where passages are processed independently in the "
                    "encoder and fused in the decoder. FiD achieves state-of-the-art results but incurs heavy "
                    "cross-attention compute cost."
                ),
                "research_question": "How can generation models attend to dozens of retrieved passages simultaneously?",
                "methodology": ["Independent encoder chunking", "Fused cross-attention decoding", "Seq2Seq generation"],
                "datasets": ["Natural Questions", "TriviaQA", "SQuAD 2.0"],
                "key_findings": [
                    "FiD scales to 100 retrieved passages, improving exact-match accuracy by 4.5%.",
                    "Cross-attention compute scales linearly with passage count, dominating total runtime.",
                ],
                "limitations": [
                    "High computational cost and GPU memory demand during multi-passage cross-attention.",
                    "High inference latency and runtime overhead when scaling beyond 50 passages.",
                    "Susceptibility to hallucinations when retrieved documents contain distractors.",
                ],
            },
            {
                "paper_id": "paper_rag_speculative",
                "title": "Speculative Verification for Retrieval-Augmented Generation",
                "authors": ["A. Leviathan", "M. Kalman", "Y. Matias"],
                "abstract": (
                    "We study draft-verification pipelines for RAG systems to accelerate token generation while "
                    "maintaining faithfulness to evidence passages."
                ),
                "research_question": "Can speculative drafting accelerate generation without compromising factual grounding?",
                "methodology": ["Speculative token drafting", "Evidence verification head", "KV-cache reuse"],
                "datasets": ["Natural Questions", "HotpotQA"],
                "key_findings": [
                    "Speculative drafting achieves 2.1x speedup on answer generation with zero loss in factual precision.",
                    "Draft acceptance rate degrades when context passages contain noisy evidence.",
                ],
                "limitations": [
                    "High inference latency remains problematic during draft verification fallbacks.",
                    "High computational cost for parallel draft model evaluation on consumer hardware.",
                    "Occasional hallucinations when context passages exhibit domain shift.",
                ],
            },
            {
                "paper_id": "paper_rag_curation",
                "title": "Active Curation and Noise Filtering for Evidence-Grounded Language Models",
                "authors": ["S. Robertson", "H. Zaragoza"],
                "abstract": (
                    "We evaluate filtering and relevance thresholding on retrieved passages before sequence decoding. "
                    "Pruning irrelevant passages reduces hallucination rate but introduces filtering latency."
                ),
                "research_question": "Does pre-filtering retrieved passages reduce downstream hallucination rates?",
                "methodology": ["Classifier-guided passage filtering", "Confidence thresholding", "Contrastive training"],
                "datasets": ["HotpotQA", "SQuAD 2.0"],
                "key_findings": [
                    "Relevance filtering eliminates 35% of distractor passages, cutting hallucination rate by 18%.",
                    "Filtering latency partially offsets the downstream decoding speedup.",
                ],
                "limitations": [
                    "High inference latency introduced by sequential passage relevance filtering.",
                    "Susceptibility to hallucinations persists when ambiguous queries bypass the filter.",
                    "High computational cost when running dense rerankers over hundreds of candidates.",
                ],
            },
        ]

    def test_complete_pipeline_sequential_execution(self, realistic_rag_papers):
        """Execute the full pipeline stage-by-stage and verify contracts at each step."""
        # Stage 1: Comparison
        comparison = compare_papers(realistic_rag_papers)
        assert isinstance(comparison, PaperComparison)
        assert len(comparison.paper_ids) == 4
        assert len(comparison.shared_themes) > 0
        assert len(comparison.shared_datasets) > 0
        assert "Natural Questions" in comparison.shared_datasets
        assert len(comparison.common_limitations) >= 2

        # Stage 2: Recurring Limitations
        recurring_limitations = find_recurring_limitations(realistic_rag_papers)
        assert isinstance(recurring_limitations, list)
        assert len(recurring_limitations) >= 2
        for rl in recurring_limitations:
            assert isinstance(rl, RecurringLimitation)
            # Each recurring limitation MUST reference at least 2 distinct papers
            assert len(rl.paper_ids) >= 2
            assert rl.frequency == len(rl.paper_ids)
            assert len(rl.evidence) >= 2

        # Stage 3: Potential Research Opportunities
        opportunities = generate_opportunities(recurring_limitations)
        assert isinstance(opportunities, list)
        assert len(opportunities) >= 2
        for opp in opportunities:
            assert isinstance(opp, ResearchOpportunity)
            assert len(opp.source_limitation_ids) >= 1
            assert len(opp.paper_ids) >= 2
            assert len(opp.evidence) >= 1
            assert opp.novelty_confidence == "Requires human validation"

        # Stage 4: Project Proposals
        proposals = generate_project_proposals(opportunities)
        assert isinstance(proposals, list)
        # Proposal count MUST be between 3 and 5
        assert 3 <= len(proposals) <= 5
        for prop in proposals:
            assert isinstance(prop, ProjectProposal)
            assert len(prop.source_opportunity_ids) >= 1
            assert len(prop.paper_ids) >= 2
            assert len(prop.evidence) >= 1
            assert prop.novelty_confidence == "Requires human validation"

    def test_complete_pipeline_via_run_pipeline(self, realistic_rag_papers):
        """Execute full pipeline via the orchestration service run_pipeline()."""
        result = run_pipeline(realistic_rag_papers)
        assert isinstance(result, PipelineResult)

        assert isinstance(result.comparison, PaperComparison)
        assert len(result.comparison.paper_ids) == 4

        assert len(result.recurring_limitations) >= 2
        assert len(result.opportunities) >= 2
        assert 3 <= len(result.proposals) <= 5

    def test_traceability_across_full_pipeline(self, realistic_rag_papers):
        """Verify unbroken lineage: proposal → opportunity → recurring limitation → supporting papers."""
        result = run_pipeline(realistic_rag_papers)

        limitation_map = {rl.limitation_id: rl for rl in result.recurring_limitations}
        opportunity_map = {opp.opportunity_id: opp for opp in result.opportunities}
        paper_id_set = {p["paper_id"] for p in realistic_rag_papers}

        for proposal in result.proposals:
            assert len(proposal.source_opportunity_ids) >= 1
            for opp_id in proposal.source_opportunity_ids:
                assert opp_id in opportunity_map
                opp = opportunity_map[opp_id]

                # Trace from opportunity to source limitations
                assert len(opp.source_limitation_ids) >= 1
                for lim_id in opp.source_limitation_ids:
                    assert lim_id in limitation_map
                    lim = limitation_map[lim_id]

                    # Trace from limitation to supporting papers
                    assert len(lim.paper_ids) >= 2
                    for pid in lim.paper_ids:
                        assert pid in paper_id_set

                    # Evidence should match paper origins
                    for ev in lim.evidence:
                        assert any(f"[{pid}]" in ev for pid in lim.paper_ids)

    def test_responsible_ai_wording_throughout_pipeline(self, realistic_rag_papers):
        """Verify strict absence of forbidden research gap and novelty claims."""
        result = run_pipeline(realistic_rag_papers)

        # Check recurring limitations
        for rl in result.recurring_limitations:
            assert "research gap" not in rl.description.lower()
            assert "novelty" not in rl.description.lower()
            assert "novel" not in rl.description.lower()

        # Check opportunities
        for opp in result.opportunities:
            assert opp.novelty_confidence == "Requires human validation"
            assert "research gap" not in opp.title.lower()
            assert "research gap" not in opp.description.lower()
            assert "novelty" not in opp.title.lower()
            assert "discovered gap" not in opp.title.lower()

        # Check proposals
        for prop in result.proposals:
            assert prop.novelty_confidence == "Requires human validation"
            combined_text = f"{prop.title} {prop.summary} {prop.problem_statement}".lower()
            assert "research gap" not in combined_text
            assert "novelty" not in combined_text
            assert "confirmed novel" not in combined_text
            assert "discovered gap" not in combined_text
            assert "guaranteed original" not in combined_text

    def test_pipeline_deterministic_behavior(self, realistic_rag_papers):
        """Executing the pipeline twice with identical inputs must produce identical outputs."""
        run1 = run_pipeline(realistic_rag_papers)
        run2 = run_pipeline(realistic_rag_papers)

        # Comparison determinism
        assert run1.comparison.paper_ids == run2.comparison.paper_ids
        assert run1.comparison.shared_themes == run2.comparison.shared_themes
        assert run1.comparison.methodological_overlaps == run2.comparison.methodological_overlaps
        assert run1.comparison.shared_datasets == run2.comparison.shared_datasets
        assert run1.comparison.common_limitations == run2.comparison.common_limitations
        assert run1.comparison.all_limitations == run2.comparison.all_limitations

        # Recurring limitations determinism
        assert len(run1.recurring_limitations) == len(run2.recurring_limitations)
        for rl1, rl2 in zip(run1.recurring_limitations, run2.recurring_limitations):
            assert rl1.limitation_id == rl2.limitation_id
            assert rl1.description == rl2.description
            assert rl1.paper_ids == rl2.paper_ids
            assert rl1.frequency == rl2.frequency
            assert rl1.severity == rl2.severity
            assert rl1.evidence == rl2.evidence

        # Opportunities determinism
        assert len(run1.opportunities) == len(run2.opportunities)
        for o1, o2 in zip(run1.opportunities, run2.opportunities):
            assert o1.opportunity_id == o2.opportunity_id
            assert o1.title == o2.title
            assert o1.description == o2.description
            assert o1.source_limitation_ids == o2.source_limitation_ids
            assert o1.keywords == o2.keywords
            assert o1.paper_ids == o2.paper_ids
            assert o1.evidence == o2.evidence
            assert o1.novelty_confidence == o2.novelty_confidence

        # Proposals determinism
        assert len(run1.proposals) == len(run2.proposals)
        for p1, p2 in zip(run1.proposals, run2.proposals):
            assert p1.proposal_id == p2.proposal_id
            assert p1.title == p2.title
            assert p1.summary == p2.summary
            assert p1.problem_statement == p2.problem_statement
            assert p1.source_opportunity_ids == p2.source_opportunity_ids
            assert p1.objectives == p2.objectives
            assert p1.proposed_methods == p2.proposed_methods
            assert p1.expected_outcomes == p2.expected_outcomes
            assert p1.technical_approach == p2.technical_approach
            assert p1.key_features == p2.key_features
            assert p1.paper_ids == p2.paper_ids
            assert p1.evidence == p2.evidence
            assert p1.novelty_confidence == p2.novelty_confidence

    def test_pipeline_edge_cases_empty_and_single(self):
        """Pipeline must gracefully reject < 2 papers with ValueError."""
        with pytest.raises(ValueError, match="At least two"):
            run_pipeline([])

        with pytest.raises(ValueError, match="At least two"):
            run_pipeline([{"paper_id": "single", "limitations": ["x"]}])

    def test_pipeline_edge_case_no_recurring_limitations(self):
        """Two papers with completely disjoint, non-recurring limitations."""
        disjoint_papers = [
            {
                "paper_id": "p_audio",
                "title": "Audio Speech Processing",
                "limitations": ["Microphone diaphragm resonance distortion"],
            },
            {
                "paper_id": "p_sat",
                "title": "Satellite Imagery Processing",
                "limitations": ["Cloud shadow occlusion artifacts"],
            },
        ]
        result = run_pipeline(disjoint_papers)
        assert isinstance(result.comparison, PaperComparison)
        # No limitation appeared in >= 2 papers
        assert result.recurring_limitations == []
        assert result.opportunities == []
        assert result.proposals == []

    def test_pipeline_edge_case_malformed_partial_inputs(self):
        """Pipeline must handle minimal/sparse paper dictionaries safely."""
        sparse_papers = [
            {"paper_id": "sparse_1"},
            {"paper_id": "sparse_2", "title": "Minimal Title"},
        ]
        result = run_pipeline(sparse_papers)
        assert isinstance(result, PipelineResult)
        assert result.comparison.paper_ids == ["sparse_1", "sparse_2"]
        assert result.recurring_limitations == []
        assert result.opportunities == []
        assert result.proposals == []


# ── M3 PaperAnalysis contract compatibility tests ────────────────────

class TestM3PaperAnalysisContract:
    """Focused tests that feed REAL M3 PaperAnalysis objects (with GroundedClaim
    and Citation) into the M4 pipeline and verify correct extraction and
    end-to-end traceability."""

    # ------------------------------------------------------------------
    # Shared fixtures
    # ------------------------------------------------------------------

    @staticmethod
    def _make_citation(paper_id: str, paper_title: str, quote: str, section: str = "Abstract") -> "Citation":
        from shared.schemas import Citation
        return Citation(
            chunk_id=f"chunk-{paper_id}-{hash(quote) & 0xFFFF:04x}",
            paper_id=paper_id,
            paper_title=paper_title,
            section=section,
            page=1,
            quote=quote,
        )

    @staticmethod
    def _make_claim(claim_text: str, paper_id: str, paper_title: str, section: str = "Abstract") -> "GroundedClaim":
        from shared.schemas import Citation, GroundedClaim
        citation = Citation(
            chunk_id=f"chunk-{paper_id}-{hash(claim_text) & 0xFFFF:04x}",
            paper_id=paper_id,
            paper_title=paper_title,
            section=section,
            page=1,
            quote=claim_text[:120],
        )
        return GroundedClaim(claim=claim_text, citations=[citation])

    @classmethod
    def _build_three_papers(cls):
        """Build 3 realistic PaperAnalysis objects with recurring limitations."""
        from shared.schemas import PaperAnalysis, GroundedClaim, Citation

        # ── Paper 1: RAG with small datasets ─────────────────────────
        p1_id = "paper-rag-lora-2024"
        p1_title = "Efficient RAG with LoRA Adapters"

        p1 = PaperAnalysis(
            paper_id=p1_id,
            paper_title=p1_title,
            problem=cls._make_claim(
                "Retrieval-augmented generation systems suffer from high computational cost "
                "when scaling to large corpora.",
                p1_id, p1_title, "Introduction",
            ),
            methodology=cls._make_claim(
                "We fine-tune a LLaMA-2 backbone with LoRA adapters combined with FAISS "
                "vector index retrieval.",
                p1_id, p1_title, "Methodology",
            ),
            dataset=cls._make_claim(
                "Experiments use SQuAD 2.0 and HotpotQA benchmarks.",
                p1_id, p1_title, "Experiments",
            ),
            results=[
                cls._make_claim(
                    "LoRA-RAG achieves 4.2% higher F1 on SQuAD 2.0 compared to the full "
                    "fine-tuning baseline.",
                    p1_id, p1_title, "Results",
                ),
            ],
            limitations=[
                cls._make_claim(
                    "Limited training data: the model was evaluated only on English benchmarks "
                    "with a small dataset of domain-specific documents.",
                    p1_id, p1_title, "Limitations",
                ),
                cls._make_claim(
                    "High computational cost of inference with large FAISS indices remains "
                    "a practical bottleneck.",
                    p1_id, p1_title, "Limitations",
                ),
            ],
            future_work=[
                cls._make_claim(
                    "Future work should explore multilingual datasets and reduced memory footprint.",
                    p1_id, p1_title, "Conclusion",
                ),
            ],
        )

        # ── Paper 2: Prompt tuning for QA ────────────────────────────
        p2_id = "paper-prompt-tuning-qa-2024"
        p2_title = "Scalable QA via Prompt Tuning on Pre-trained LLMs"

        p2 = PaperAnalysis(
            paper_id=p2_id,
            paper_title=p2_title,
            problem=cls._make_claim(
                "Current QA systems require expensive full fine-tuning, limiting accessibility.",
                p2_id, p2_title, "Introduction",
            ),
            methodology=cls._make_claim(
                "Soft prompt tokens are prepended to frozen GPT-4 weights; retrieval uses "
                "BM25 sparse retrieval.",
                p2_id, p2_title, "Methodology",
            ),
            dataset=cls._make_claim(
                "TriviaQA, SQuAD 2.0, and WebQuestions are used as evaluation benchmarks.",
                p2_id, p2_title, "Experiments",
            ),
            results=[
                cls._make_claim(
                    "Prompt-tuned models match full fine-tune accuracy while using 10× less GPU memory.",
                    p2_id, p2_title, "Results",
                ),
            ],
            limitations=[
                cls._make_claim(
                    "Small dataset availability for low-resource languages severely limits "
                    "generalization to non-English QA tasks.",
                    p2_id, p2_title, "Limitations",
                ),
                cls._make_claim(
                    "High computational cost of prompt search during soft-prompt optimization.",
                    p2_id, p2_title, "Limitations",
                ),
                cls._make_claim(
                    "Model interpretability is limited because soft prompts are opaque "
                    "continuous embeddings with no natural language meaning.",
                    p2_id, p2_title, "Limitations",
                ),
            ],
            future_work=[
                cls._make_claim(
                    "Improving data efficiency and reducing annotation cost are key directions.",
                    p2_id, p2_title, "Conclusion",
                ),
            ],
        )

        # ── Paper 3: Knowledge distillation for edge NLP ─────────────
        p3_id = "paper-kd-edge-nlp-2024"
        p3_title = "Knowledge Distillation for Edge NLP Inference"

        p3 = PaperAnalysis(
            paper_id=p3_id,
            paper_title=p3_title,
            problem=cls._make_claim(
                "Deploying large language models on edge devices is prohibitively expensive "
                "due to hardware constraints.",
                p3_id, p3_title, "Introduction",
            ),
            methodology=cls._make_claim(
                "Teacher-student distillation compresses BERT-large into a 6-layer student "
                "using mean-squared-error knowledge transfer.",
                p3_id, p3_title, "Methodology",
            ),
            dataset=cls._make_claim(
                "GLUE benchmark suite and a proprietary customer-support dataset are used.",
                p3_id, p3_title, "Experiments",
            ),
            results=[
                cls._make_claim(
                    "The distilled model retains 95% of teacher accuracy at 4× faster inference.",
                    p3_id, p3_title, "Results",
                ),
            ],
            limitations=[
                cls._make_claim(
                    "Insufficient training data for low-resource domains limits the student "
                    "model performance in specialized settings.",
                    p3_id, p3_title, "Limitations",
                ),
                cls._make_claim(
                    "High computational cost of the distillation process itself requires "
                    "multi-GPU clusters.",
                    p3_id, p3_title, "Limitations",
                ),
                cls._make_claim(
                    "Limited model interpretability: the black-box nature of the distilled "
                    "network makes debugging difficult.",
                    p3_id, p3_title, "Limitations",
                ),
            ],
            future_work=[
                cls._make_claim(
                    "Exploring data-efficient distillation and hardware-aware pruning are "
                    "promising future directions.",
                    p3_id, p3_title, "Conclusion",
                ),
            ],
        )

        return [p1, p2, p3]

    # ------------------------------------------------------------------
    # Unit: _extract_claim_text with GroundedClaim
    # ------------------------------------------------------------------

    def test_extract_claim_text_from_grounded_claim(self):
        """_extract_claim_text must return GroundedClaim.claim correctly."""
        from backend.app.research_intelligence.comparison import _extract_claim_text
        from backend.app.research_intelligence.limitations import _extract_claim_text as lim_extract
        from shared.schemas import GroundedClaim, Citation

        cit = Citation(
            chunk_id="c1", paper_id="p1", paper_title="T1",
            section="Abstract", page=1, quote="Supporting quote.",
        )
        gc = GroundedClaim(claim="Small dataset limits generalization.", citations=[cit])

        # comparison module
        assert _extract_claim_text(gc) == "Small dataset limits generalization."
        # limitations module
        assert lim_extract(gc) == "Small dataset limits generalization."

    def test_extract_claim_text_text_property(self):
        """GroundedClaim.text property must also be accepted (alias for .claim)."""
        from backend.app.research_intelligence.comparison import _extract_claim_text
        from shared.schemas import GroundedClaim, Citation

        cit = Citation(
            chunk_id="c2", paper_id="p2", paper_title="T2",
            section="Body", page=2, quote="Quote text.",
        )
        gc = GroundedClaim(claim="High compute overhead is prohibitive.", citations=[cit])
        # .text is a property that returns .claim
        assert gc.text == gc.claim
        assert _extract_claim_text(gc) == "High compute overhead is prohibitive."

    def test_extract_claim_text_plain_string_still_works(self):
        """Plain strings must still be returned unchanged."""
        from backend.app.research_intelligence.comparison import _extract_claim_text
        assert _extract_claim_text("plain string") == "plain string"

    def test_extract_claim_text_dict_still_works(self):
        """Dicts with 'claim' key must still be handled."""
        from backend.app.research_intelligence.comparison import _extract_claim_text
        assert _extract_claim_text({"claim": "dict claim text"}) == "dict claim text"
        assert _extract_claim_text({"text": "dict text value"}) == "dict text value"

    def test_extract_claim_text_none_returns_empty(self):
        """None input must return empty string."""
        from backend.app.research_intelligence.comparison import _extract_claim_text
        assert _extract_claim_text(None) == ""

    # ------------------------------------------------------------------
    # Unit: compare_papers with PaperAnalysis
    # ------------------------------------------------------------------

    def test_compare_papers_accepts_paper_analysis_objects(self):
        """compare_papers must accept real PaperAnalysis objects."""
        papers = self._build_three_papers()
        result = compare_papers(papers)

        assert isinstance(result, PaperComparison)
        assert set(result.paper_ids) == {
            "paper-rag-lora-2024",
            "paper-prompt-tuning-qa-2024",
            "paper-kd-edge-nlp-2024",
        }

    def test_compare_papers_extracts_paper_ids(self):
        """paper_id fields from PaperAnalysis must be preserved in comparison."""
        papers = self._build_three_papers()
        result = compare_papers(papers)

        assert "paper-rag-lora-2024" in result.paper_ids
        assert "paper-prompt-tuning-qa-2024" in result.paper_ids
        assert "paper-kd-edge-nlp-2024" in result.paper_ids

    def test_compare_papers_grounded_claim_limitations_extracted(self):
        """GroundedClaim.claim text must appear in all_limitations."""
        papers = self._build_three_papers()
        result = compare_papers(papers)

        joined = " ".join(result.all_limitations)
        assert "small dataset" in joined.lower() or "limited training data" in joined.lower() \
            or "insufficient" in joined.lower()
        assert "computational cost" in joined.lower() or "compute" in joined.lower()

    def test_compare_papers_grounded_claim_methodology_extracted(self):
        """GroundedClaim.claim from methodology field must appear in methodological results."""
        papers = self._build_three_papers()
        result = compare_papers(papers)

        # methodology is a single GroundedClaim; its text should surface somewhere
        all_method_text = " ".join(result.methodological_overlaps + result.methodological_differences)
        assert len(all_method_text) > 0  # at least something was extracted

    def test_compare_papers_dataset_grounded_claim_extracted(self):
        """GroundedClaim.claim from dataset field contributes to dataset comparison."""
        papers = self._build_three_papers()
        result = compare_papers(papers)

        all_ds = " ".join(result.shared_datasets + result.dataset_differences)
        # SQuAD 2.0 appears in paper 1 and paper 2 dataset claims
        assert "SQuAD" in all_ds

    # ------------------------------------------------------------------
    # Unit: find_recurring_limitations with PaperAnalysis
    # ------------------------------------------------------------------

    def test_find_recurring_limitations_accepts_paper_analysis(self):
        """find_recurring_limitations must accept PaperAnalysis objects."""
        papers = self._build_three_papers()
        recurring = find_recurring_limitations(papers)

        assert isinstance(recurring, list)
        assert all(isinstance(r, RecurringLimitation) for r in recurring)

    def test_recurring_limitations_detected_from_grounded_claims(self):
        """Recurring limitations must be detected from GroundedClaim.claim text."""
        papers = self._build_three_papers()
        recurring = find_recurring_limitations(papers)

        assert len(recurring) >= 1, "Expected at least one recurring limitation across 3 papers"

        # All three papers mention 'data scarcity' / 'limited data'
        descriptions = [r.description.lower() for r in recurring]
        assert any(
            "data" in d or "compute" in d or "computational" in d or "interpretab" in d
            for d in descriptions
        ), f"Expected a known recurring concept in: {descriptions}"

    def test_recurring_limitations_minimum_two_papers(self):
        """Every recurring limitation must appear in at least 2 distinct papers."""
        papers = self._build_three_papers()
        recurring = find_recurring_limitations(papers)

        for r in recurring:
            assert r.frequency >= 2, (
                f"Limitation '{r.description}' has frequency {r.frequency} < 2"
            )
            assert len(r.paper_ids) >= 2, (
                f"Limitation '{r.description}' references only {len(r.paper_ids)} paper(s)"
            )

    def test_recurring_limitations_paper_ids_traceable(self):
        """paper_ids on each recurring limitation must be valid paper IDs."""
        papers = self._build_three_papers()
        valid_ids = {"paper-rag-lora-2024", "paper-prompt-tuning-qa-2024", "paper-kd-edge-nlp-2024"}
        recurring = find_recurring_limitations(papers)

        for r in recurring:
            for pid in r.paper_ids:
                assert pid in valid_ids, (
                    f"Unknown paper_id '{pid}' in limitation '{r.description}'"
                )

    def test_recurring_limitations_evidence_contains_paper_ids(self):
        """Evidence strings must be prefixed with [paper_id]."""
        papers = self._build_three_papers()
        recurring = find_recurring_limitations(papers)

        for r in recurring:
            for ev in r.evidence:
                assert ev.startswith("["), f"Evidence missing [paper_id] prefix: {ev!r}"

    def test_recurring_limitations_citations_not_invented(self):
        """M4 must NOT add citations that were not in M3 GroundedClaim objects."""
        # RecurringLimitation.evidence only contains text excerpts, no new citations
        papers = self._build_three_papers()
        recurring = find_recurring_limitations(papers)

        for r in recurring:
            # evidence is plain text, not Citation objects
            for ev in r.evidence:
                assert isinstance(ev, str), (
                    f"Evidence should be str, got {type(ev)} in '{r.description}'"
                )

    # ------------------------------------------------------------------
    # Integration: full pipeline PaperAnalysis → proposals
    # ------------------------------------------------------------------

    def test_full_pipeline_with_paper_analysis_objects(self):
        """Full pipeline must work end-to-end with PaperAnalysis inputs."""
        papers = self._build_three_papers()

        # Step 1: compare
        comparison = compare_papers(papers)
        assert isinstance(comparison, PaperComparison)

        # Step 2: recurring limitations
        recurring = find_recurring_limitations(papers)
        assert isinstance(recurring, list)

        # Step 3: opportunities
        opportunities = generate_opportunities(recurring)
        assert isinstance(opportunities, list)

        # Step 4: proposals
        proposals = generate_project_proposals(opportunities)
        assert isinstance(proposals, list)

    def test_pipeline_generates_opportunities_from_paper_analysis(self):
        """Opportunities must be generated when recurring limitations exist."""
        papers = self._build_three_papers()
        recurring = find_recurring_limitations(papers)

        if recurring:
            opportunities = generate_opportunities(recurring)
            assert len(opportunities) >= 1
            for opp in opportunities:
                assert isinstance(opp, ResearchOpportunity)

    def test_pipeline_generates_proposals_from_paper_analysis(self):
        """Project proposals must be generated when opportunities exist."""
        papers = self._build_three_papers()
        recurring = find_recurring_limitations(papers)
        opportunities = generate_opportunities(recurring)

        if opportunities:
            proposals = generate_project_proposals(opportunities)
            assert len(proposals) >= 1
            for prop in proposals:
                assert isinstance(prop, ProjectProposal)

    def test_novelty_confidence_invariant(self):
        """novelty_confidence must be exactly 'Requires human validation' throughout."""
        papers = self._build_three_papers()
        recurring = find_recurring_limitations(papers)
        opportunities = generate_opportunities(recurring)
        proposals = generate_project_proposals(opportunities)

        for opp in opportunities:
            assert opp.novelty_confidence == "Requires human validation", (
                f"Opportunity '{opp.title}' has novelty_confidence={opp.novelty_confidence!r}"
            )
        for prop in proposals:
            assert prop.novelty_confidence == "Requires human validation", (
                f"Proposal '{prop.title}' has novelty_confidence={prop.novelty_confidence!r}"
            )

    def test_pipeline_paper_ids_traceable_in_comparison(self):
        """All input paper IDs must survive into the comparison output."""
        papers = self._build_three_papers()
        comparison = compare_papers(papers)

        input_ids = {p.paper_id for p in papers}
        for pid in input_ids:
            assert pid in comparison.paper_ids, (
                f"paper_id '{pid}' lost during compare_papers()"
            )

    def test_pipeline_paper_ids_traceable_in_recurring_limitations(self):
        """paper_ids in recurring limitations must be a subset of input paper IDs."""
        papers = self._build_three_papers()
        input_ids = {p.paper_id for p in papers}
        recurring = find_recurring_limitations(papers)

        for r in recurring:
            for pid in r.paper_ids:
                assert pid in input_ids, (
                    f"Spurious paper_id '{pid}' appeared in recurring limitation '{r.description}'"
                )

    # ------------------------------------------------------------------
    # Compatibility: existing input types still work alongside PaperAnalysis
    # ------------------------------------------------------------------

    def test_plain_string_and_paper_analysis_mixed_not_required(self):
        """Alias / backwards-compat: plain-string papers still accepted by both
        comparison and limitations helpers independently."""
        from backend.app.research_intelligence.comparison import _extract_paper_record
        from backend.app.research_intelligence.limitations import _extract_paper_limitations

        # plain string
        pid, lims = _extract_paper_limitations("a plain string paper", 0)
        assert pid == "a plain string paper"
        assert lims == []

        rec = _extract_paper_record("another string", 1)
        assert rec["paper_id"] == "another string"

    def test_generic_object_with_claim_attribute(self):
        """Generic objects with a .claim attribute must be handled by _extract_claim_text."""
        from backend.app.research_intelligence.comparison import _extract_claim_text

        class FakeClaim:
            claim = "Fake claim from generic object."

        assert _extract_claim_text(FakeClaim()) == "Fake claim from generic object."

    def test_grounded_claim_in_list_via_to_string_list(self):
        """_to_string_list must unwrap a list of GroundedClaim objects correctly."""
        from backend.app.research_intelligence.comparison import _to_string_list
        from shared.schemas import GroundedClaim, Citation

        def _cit(n):
            return Citation(
                chunk_id=f"c{n}", paper_id="px", paper_title="TX",
                section="S", page=1, quote=f"quote {n}",
            )

        claims = [
            GroundedClaim(claim="First limitation claim.", citations=[_cit(1)]),
            GroundedClaim(claim="Second limitation claim.", citations=[_cit(2)]),
        ]
        result = _to_string_list(claims)
        assert result == ["First limitation claim.", "Second limitation claim."]
