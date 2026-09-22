import pytest

from backend.app.agents.analyzer import PaperAnalyzer
from shared.schemas import EvidenceChunk


class MockLLMService:
    def generate(self, prompt, system_prompt=None, temperature=0.0):
        return """
        {
            "problem": {
                "text": "The paper addresses limited accuracy in image classification.",
                "evidence_ids": ["chunk-2"]
            },
            "objective": {
                "text": "The study aims to improve image classification accuracy.",
                "evidence_ids": ["chunk-2"]
            },
            "methodology": {
                "text": "The authors train and evaluate a convolutional neural network for image classification.",
                "evidence_ids": ["chunk-1"]
            },
            "dataset": {
                "text": "The evaluation uses an image classification dataset.",
                "evidence_ids": ["chunk-2"]
            },
            "models": {
                "text": "A convolutional neural network is used.",
                "evidence_ids": ["chunk-1"]
            },
            "results": [
                {
                    "text": "The proposed approach improves classification accuracy.",
                    "evidence_ids": ["chunk-2"]
                }
            ],
            "limitations": [
                {
                    "text": "The evaluation is limited to the selected dataset.",
                    "evidence_ids": ["chunk-2"]
                }
            ],
            "future_work": [
                {
                    "text": "The authors suggest evaluating the approach on additional datasets.",
                    "evidence_ids": ["chunk-2"]
                }
            ]
        }
        """


def test_paper_analyzer():
    evidence = [
        EvidenceChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            paper_title="Test Research Paper",
            section="Methodology",
            page=4,
            text=(
                "The authors train a convolutional neural network "
                "for image classification."
            ),
        ),
        EvidenceChunk(
            chunk_id="chunk-2",
            paper_id="paper-1",
            paper_title="Test Research Paper",
            section="Results",
            page=7,
            text=(
                "The proposed approach improves classification accuracy "
                "on the evaluation dataset."
            ),
        ),
    ]

    analyzer = PaperAnalyzer(MockLLMService())

    result = analyzer.analyze(
        paper_id="paper-1",
        paper_title="Test Research Paper",
        evidence=evidence,
    )

    assert result.paper_id == "paper-1"
    assert result.paper_title == "Test Research Paper"

    assert result.problem is not None
    assert result.objective is not None
    assert result.methodology is not None
    assert result.dataset is not None
    assert result.models is not None

    assert len(result.results) == 1
    assert len(result.limitations) == 1
    assert len(result.future_work) == 1

    assert "classification" in result.methodology.text.lower()

    assert result.methodology.citations[0].chunk_id == "chunk-1"
    assert result.methodology.citations[0].section == "Methodology"
    assert result.methodology.citations[0].page == 4

    assert result.results[0].citations[0].chunk_id == "chunk-2"
    assert result.results[0].citations[0].section == "Results"
    assert result.results[0].citations[0].page == 7

def test_paper_analyzer_rejects_unknown_evidence_id():
    class BadLLMService:
        def generate(self, prompt, system_prompt=None, temperature=0.0):
            return """
            {
                "problem": {
                    "text": "This claim is not supported.",
                    "evidence_ids": ["fake-chunk"]
                }
            }
            """

    evidence = [
        EvidenceChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            paper_title="Test Research Paper",
            section="Introduction",
            page=2,
            text="The paper discusses image classification.",
        )
    ]

    analyzer = PaperAnalyzer(BadLLMService())

    with pytest.raises(ValueError, match="unknown evidence ID"):
        analyzer.analyze(
            paper_id="paper-1",
            paper_title="Test Research Paper",
            evidence=evidence,
        )


def test_paper_analyzer_retries_once_after_hallucinated_evidence_id():
    """First attempt references a made-up evidence ID (as real LLMs do
    occasionally); the retry uses a valid one. Analysis should succeed
    without surfacing a 400 to the caller."""

    class FlakyLLMService:
        def __init__(self):
            self.calls: list[str] = []

        def generate(self, prompt, system_prompt=None, temperature=0.0):
            self.calls.append(prompt)
            evidence_id = "chunk-1" if "IMPORTANT CORRECTION" in prompt else "66"
            return f"""
            {{
                "problem": {{
                    "text": "The paper addresses limited accuracy in image classification.",
                    "evidence_ids": ["{evidence_id}"]
                }}
            }}
            """

    evidence = [
        EvidenceChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            paper_title="Test Research Paper",
            section="Introduction",
            page=2,
            text="The paper discusses image classification.",
        )
    ]

    llm = FlakyLLMService()
    analyzer = PaperAnalyzer(llm)

    result = analyzer.analyze(
        paper_id="paper-1",
        paper_title="Test Research Paper",
        evidence=evidence,
    )

    assert len(llm.calls) == 2
    assert "IMPORTANT CORRECTION" in llm.calls[1]
    assert result.problem is not None
    assert result.problem.citations[0].chunk_id == "chunk-1"


def test_paper_analyzer_drops_claims_without_evidence_but_keeps_the_rest():
    class MixedLLMService:
        def generate(self, prompt, system_prompt=None, temperature=0.0):
            return """
            {
                "problem": {
                    "text": "Image classification is studied.",
                    "evidence_ids": ["chunk-1"]
                },
                "dataset": {
                    "text": "The paper does not mention any specific dataset.",
                    "evidence_ids": []
                },
                "limitations": [
                    {"text": "Grounded limitation.", "evidence_ids": ["chunk-1"]},
                    {"text": "Ungrounded limitation.", "evidence_ids": []}
                ]
            }
            """

    evidence = [
        EvidenceChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            paper_title="Test Research Paper",
            section="Introduction",
            page=2,
            text="The paper discusses image classification.",
        )
    ]

    analysis = PaperAnalyzer(MixedLLMService()).analyze(
        paper_id="paper-1",
        paper_title="Test Research Paper",
        evidence=evidence,
    )

    assert analysis.problem is not None
    assert analysis.problem.citations[0].chunk_id == "chunk-1"
    assert analysis.dataset is None
    assert [c.claim for c in analysis.limitations] == ["Grounded limitation."]
    assert all(c.citations for c in analysis.limitations)


def test_analyzer_rejects_unknown_evidence_id():
    evidence = [
        EvidenceChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            paper_title="Test Paper",
            section="Methodology",
            page=4,
            text="The proposed method uses a transformer architecture.",
        )
    ]

    class MockLLMService:
        def generate(
            self,
            prompt,
            system_prompt=None,
            temperature=0.0,
        ):
            return """
            {
                "problem": {
                    "text": "The paper studies a research problem.",
                    "evidence_ids": ["fake-chunk-999"]
                },
                "objective": null,
                "methodology": null,
                "dataset": null,
                "models": null,
                "results": [],
                "limitations": [],
                "future_work": []
            }
            """

    analyzer = PaperAnalyzer(MockLLMService())

    with pytest.raises(
        ValueError,
        match="unknown evidence ID",
    ):
        analyzer.analyze(
            paper_id="paper-1",
            paper_title="Test Paper",
            evidence=evidence,
        )