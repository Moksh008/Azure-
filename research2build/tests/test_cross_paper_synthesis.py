import json
import re

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.llm_factory import get_llm_service
from shared.schemas import EvidenceChunk


class _TwoCallLLM:
    def __init__(self):
        self.calls: list[str] = []

    def generate(self, prompt, system_prompt=None, temperature=0.0):
        self.calls.append(prompt)
        if "router for a research-paper assistant" in prompt:
            return json.dumps({"intent": "analyze", "paper_id": None})

        evidence_ids = re.findall(r"^\[([^\]]+)\]", prompt, flags=re.MULTILINE)
        paper_ids = re.findall(r"^Paper ID: ([^\n]+)", prompt, flags=re.MULTILINE)
        return json.dumps(
            {
                "overall_summary": "The papers use different retrieval architectures.",
                "paper_analyses": [
                    {
                        "paper_id": paper_id,
                        "paper_title": f"Paper {index}",
                        "approach_architecture": "Retrieval architecture.",
                        "key_difference": "A paper-specific design choice.",
                        "evidence_ids": [evidence_ids[index - 1]],
                    }
                    for index, paper_id in enumerate(paper_ids, start=1)
                ],
                "comparison": {
                    "common_patterns": ["Retrieval is used."],
                    "architectural_differences": ["The architectures differ."],
                },
            }
        )


class _MismatchedThenFixedLLM:
    """First synthesis attempt swaps evidence IDs between papers; retry fixes it."""

    def __init__(self):
        self.calls: list[str] = []

    def generate(self, prompt, system_prompt=None, temperature=0.0):
        self.calls.append(prompt)
        if "router for a research-paper assistant" in prompt:
            return json.dumps({"intent": "analyze", "paper_id": None})

        evidence_ids = re.findall(r"^\[([^\]]+)\]", prompt, flags=re.MULTILINE)
        paper_ids = re.findall(r"^Paper ID: ([^\n]+)", prompt, flags=re.MULTILINE)
        is_retry = "IMPORTANT CORRECTION" in prompt
        assigned_ids = (
            evidence_ids
            if is_retry
            else list(reversed(evidence_ids))
        )
        return json.dumps(
            {
                "overall_summary": "The papers use different retrieval architectures.",
                "paper_analyses": [
                    {
                        "paper_id": paper_id,
                        "paper_title": f"Paper {index}",
                        "approach_architecture": "Retrieval architecture.",
                        "key_difference": "A paper-specific design choice.",
                        "evidence_ids": [assigned_ids[index - 1]],
                    }
                    for index, paper_id in enumerate(paper_ids, start=1)
                ],
                "comparison": {
                    "common_patterns": ["Retrieval is used."],
                    "architectural_differences": ["The architectures differ."],
                },
            }
        )


def test_cross_paper_synthesis_retries_once_after_evidence_paper_mismatch():
    llm = _MismatchedThenFixedLLM()
    app.dependency_overrides[get_llm_service] = lambda: llm
    try:
        papers = [_paper_chunks(number) for number in range(1, 3)]
        response = TestClient(app).post(
            "/chat",
            json={
                "message": "Compare the architectural differences across these papers.",
                "library": [
                    {
                        "paper_id": chunk.paper_id,
                        "title": chunk.paper_title,
                        "source": "upload",
                    }
                    for chunk in papers
                ],
                "evidence": [chunk.model_dump() for chunk in papers],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    # router call + failed synthesis attempt + corrected retry
    assert len(llm.calls) == 3
    assert "IMPORTANT CORRECTION" in llm.calls[2]

    citations = response.json()["analyses"][0]["problem"]["citations"]
    assert {citation["paper_id"] for citation in citations} == {"paper-1", "paper-2"}


def _paper_chunks(paper_number: int) -> EvidenceChunk:
    return EvidenceChunk(
        chunk_id=f"paper-{paper_number}-chunk-1",
        paper_id=f"paper-{paper_number}",
        paper_title=f"Paper {paper_number}",
        section="Architecture",
        page=paper_number + 1,
        text=f"Paper {paper_number} describes its retrieval architecture.",
    )


def test_multi_paper_chat_uses_one_synthesis_call_and_preserves_provenance():
    llm = _TwoCallLLM()
    app.dependency_overrides[get_llm_service] = lambda: llm
    try:
        papers = [_paper_chunks(number) for number in range(1, 6)]
        response = TestClient(app).post(
            "/chat",
            json={
                "message": "Compare the architectural differences across these papers.",
                "library": [
                    {
                        "paper_id": chunk.paper_id,
                        "title": chunk.paper_title,
                        "source": "upload",
                    }
                    for chunk in papers
                ],
                "evidence": [chunk.model_dump() for chunk in papers],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    assert len(llm.calls) == 2
    for paper_number in range(1, 6):
        assert f"Paper ID: paper-{paper_number}" in llm.calls[1]
    assert "paper-1-chunk-1" in llm.calls[1]
    assert "paper-5-chunk-1" in llm.calls[1]

    analysis = response.json()["analyses"][0]
    citation_data = analysis["problem"]["citations"]
    cited_papers = {citation["paper_id"] for citation in citation_data}
    assert len(cited_papers) >= 4
    assert cited_papers == {
        "paper-1",
        "paper-2",
        "paper-3",
        "paper-4",
        "paper-5",
    }
    assert {citation["page"] for citation in citation_data} == {2, 3, 4, 5, 6}
    assert {citation["section"] for citation in citation_data} == {"Architecture"}
    assert {citation["chunk_id"] for citation in citation_data} == {
        "paper-1-chunk-1",
        "paper-2-chunk-1",
        "paper-3-chunk-1",
        "paper-4-chunk-1",
        "paper-5-chunk-1",
    }
    assert {citation["quote"] for citation in citation_data} == {
        "Paper 1 describes its retrieval architecture.",
        "Paper 2 describes its retrieval architecture.",
        "Paper 3 describes its retrieval architecture.",
        "Paper 4 describes its retrieval architecture.",
        "Paper 5 describes its retrieval architecture.",
    }


class _BalancedTwoCallLLM(_TwoCallLLM):
    def generate(self, prompt, system_prompt=None, temperature=0.0):
        self.calls.append(prompt)
        if "router for a research-paper assistant" in prompt:
            return json.dumps({"intent": "analyze", "paper_id": None})

        evidence_ids = re.findall(r"^\[([^\]]+)\]", prompt, flags=re.MULTILINE)
        paper_ids = re.findall(r"^Paper ID: ([^\n]+)", prompt, flags=re.MULTILINE)
        one_per_paper = []
        for evidence_id in evidence_ids:
            paper_id = evidence_id.split("-chunk-", 1)[0]
            if paper_id not in {item.split("-chunk-", 1)[0] for item in one_per_paper}:
                one_per_paper.append(evidence_id)
        return json.dumps(
            {
                "overall_summary": "The papers compare different retrieval architectures.",
                "paper_analyses": [
                    {
                        "paper_id": paper_id,
                        "paper_title": f"Paper {index}",
                        "approach_architecture": "Retrieval architecture.",
                        "key_difference": "A paper-specific design choice.",
                        "evidence_ids": [
                            next(item for item in one_per_paper if item.startswith(paper_id + "-"))
                        ],
                    }
                    for index, paper_id in enumerate(paper_ids, start=1)
                ],
                "comparison": {
                    "common_patterns": ["Retrieval is used."],
                    "architectural_differences": ["The architectures differ."],
                },
            }
        )


def test_balanced_synthesis_limits_context_per_paper_and_keeps_all_labels():
    llm = _BalancedTwoCallLLM()
    app.dependency_overrides[get_llm_service] = lambda: llm
    try:
        chunks = []
        for paper_number in range(1, 6):
            for chunk_number in range(1, 4):
                chunks.append(
                    EvidenceChunk(
                        chunk_id=f"paper-{paper_number}-chunk-{chunk_number}",
                        paper_id=f"paper-{paper_number}",
                        paper_title=f"Paper {paper_number}",
                        section="Architecture",
                        page=paper_number + chunk_number,
                        text=(
                            f"Paper {paper_number} discusses retrieval architecture "
                            f"comparison detail {chunk_number}."
                        ),
                    )
                )
        response = TestClient(app).post(
            "/chat",
            json={
                "message": "Compare retrieval architecture differences across these papers.",
                "library": [
                    {"paper_id": f"paper-{n}", "title": f"Paper {n}", "source": "upload"}
                    for n in range(1, 6)
                ],
                "evidence": [chunk.model_dump() for chunk in chunks],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    assert len(llm.calls) == 2
    synthesis_prompt = llm.calls[1]
    assert sum(synthesis_prompt.count(f"Paper ID: paper-{n}") for n in range(1, 6)) == 5
    assert len(re.findall(r"^\[([^\]]+)\]", synthesis_prompt, flags=re.MULTILINE)) <= 10
    for paper_number in range(1, 6):
        paper_chunks = re.findall(
            rf"^\[paper-{paper_number}-chunk-[^\]]+\]",
            synthesis_prompt,
            flags=re.MULTILINE,
        )
        assert len(paper_chunks) <= 2

    citations = response.json()["analyses"][0]["problem"]["citations"]
    assert {citation["paper_id"] for citation in citations} == {
        f"paper-{n}" for n in range(1, 6)
    }
    assert all(citation["section"] == "Architecture" for citation in citations)
    assert all(citation["quote"].startswith("Paper ") for citation in citations)
