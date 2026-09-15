from backend.app.agents.analyzer import PaperAnalyzer
from shared.schemas import EvidenceChunk


class MockLLMService:
    def generate(self, prompt, system_prompt=None, temperature=0.0):
        return """
        {
            "problem": "The paper addresses limited accuracy in image classification.",
            "objective": "The study aims to improve image classification accuracy.",
            "methodology": "The authors train and evaluate a convolutional neural network for image classification.",
            "dataset": "The evaluation uses an image classification dataset.",
            "models": "A convolutional neural network is used.",
            "results": [
                "The proposed approach improves classification accuracy."
            ],
            "limitations": [
                "The evaluation is limited to the selected dataset."
            ],
            "future_work": [
                "The authors suggest evaluating the approach on additional datasets."
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