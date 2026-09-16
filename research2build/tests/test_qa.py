import pytest

from backend.app.agents.qa import GroundedQA
from shared.schemas import EvidenceChunk


class MockLLMService:
    def generate(self, prompt, system_prompt=None, temperature=0.0):
        return """
        {
            "answer": "The authors use an image classification dataset for evaluation.",
            "evidence_ids": ["chunk-2"],
            "evidence_sufficient": true
        }
        """


def test_grounded_qa_returns_cited_answer():
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
            section="Dataset",
            page=5,
            text="The evaluation uses an image classification dataset.",
        ),
    ]

    qa = GroundedQA(MockLLMService())

    result = qa.answer(
        question="What dataset did the authors use?",
        evidence=evidence,
    )

    assert result.answer == (
        "The authors use an image classification dataset for evaluation."
    )

    assert result.evidence_sufficient is True

    assert len(result.citations) == 1
    assert result.citations[0].chunk_id == "chunk-2"
    assert result.citations[0].section == "Dataset"
    assert result.citations[0].page == 5


def test_grounded_qa_rejects_unknown_evidence_id():
    class BadLLMService:
        def generate(self, prompt, system_prompt=None, temperature=0.0):
            return """
            {
                "answer": "The paper uses a special dataset.",
                "evidence_ids": ["fake-chunk"],
                "evidence_sufficient": true
            }
            """

    evidence = [
        EvidenceChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            paper_title="Test Research Paper",
            section="Dataset",
            page=5,
            text="The evaluation uses an image classification dataset.",
        )
    ]

    qa = GroundedQA(BadLLMService())

    with pytest.raises(ValueError, match="unknown evidence ID"):
        qa.answer(
            question="What dataset did the authors use?",
            evidence=evidence,
        )


def test_grounded_qa_rejects_empty_question():
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

    qa = GroundedQA(MockLLMService())

    with pytest.raises(ValueError, match="Question cannot be empty"):
        qa.answer(
            question="   ",
            evidence=evidence,
        )


def test_grounded_qa_handles_no_evidence():
    qa = GroundedQA(MockLLMService())

    result = qa.answer(
        question="What dataset did the authors use?",
        evidence=[],
    )

    assert result.evidence_sufficient is False
    assert result.citations == []
    assert "not find enough evidence" in result.answer.lower()

def test_grounded_qa_rejects_sufficient_answer_without_citations():
    class BadLLMService:
        def generate(self, prompt, system_prompt=None, temperature=0.0):
            return """
            {
                "answer": "The authors use an image classification dataset.",
                "evidence_ids": [],
                "evidence_sufficient": true
            }
            """

    evidence = [
        EvidenceChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            paper_title="Test Research Paper",
            section="Dataset",
            page=5,
            text="The evaluation uses an image classification dataset.",
        )
    ]

    qa = GroundedQA(BadLLMService())

    with pytest.raises(
        ValueError,
        match="Sufficient answer must contain evidence citations",
    ):
        qa.answer(
            question="What dataset did the authors use?",
            evidence=evidence,
        )