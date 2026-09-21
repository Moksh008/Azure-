"""Relevant-chunk selection for chat: ranking, fairness, budget, and wiring."""

import json
import re

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.evidence_selection import select_evidence
from backend.app.services.llm_factory import get_llm_service
from shared.schemas import EvidenceChunk


def _chunk(paper_id: str, n: int, text: str) -> EvidenceChunk:
    return EvidenceChunk(
        chunk_id=f"{paper_id}-{n:03d}",
        paper_id=paper_id,
        paper_title=f"Paper {paper_id}",
        section=None,
        page=n + 1,
        text=text,
    )


def _filler(paper_id: str, count: int, size: int = 500) -> list[EvidenceChunk]:
    return [
        _chunk(paper_id, n, f"generic background discussion number {n}. " * (size // 45))
        for n in range(count)
    ]


def test_small_evidence_passes_through_untouched():
    chunks = [_chunk("a", 0, "short text"), _chunk("a", 1, "more short text")]
    assert select_evidence(chunks, "anything", budget=10_000) == chunks


def test_picks_the_chunk_that_answers_the_question():
    chunks = _filler("a", 40)
    chunks[27] = _chunk("a", 27, "The proposed optimizer reduced training energy by 41 percent.")
    selected = select_evidence(chunks, "how much energy did the optimizer save?", budget=1500)
    assert chunks[27] in selected
    assert sum(len(c.text) for c in selected) <= 1500 + len(chunks[27].text)


def test_output_keeps_document_order_and_original_objects():
    chunks = _filler("a", 30)
    chunks[20] = _chunk("a", 20, "zebra migration patterns observed")
    chunks[5] = _chunk("a", 5, "zebra herd size estimates")
    selected = select_evidence(chunks, "zebra", budget=1200)
    assert [c.chunk_id for c in selected] == sorted(c.chunk_id for c in selected)
    assert all(any(c is original for original in chunks) for c in selected)


def test_every_paper_gets_a_chunk_before_any_gets_a_second():
    strong = [_chunk("a", n, f"quantum annealing result {n} " * 20) for n in range(10)]
    weak = _filler("b", 10) + [_chunk("b", 99, "one quantum annealing mention here")]
    selected = select_evidence(strong + weak, "quantum annealing", budget=1600)
    assert {c.paper_id for c in selected} == {"a", "b"}


def test_question_with_no_keyword_overlap_falls_back_to_opening_chunks():
    chunks = _filler("a", 30)
    selected = select_evidence(chunks, "what is this paper about?", budget=1200)
    assert [c.chunk_id for c in selected][:2] == ["a-000", "a-001"]


def test_lead_chunks_are_always_included():
    chunks = _filler("a", 30)
    chunks[25] = _chunk("a", 25, "limitations of the approach include latency")
    selected = select_evidence(chunks, "limitations latency", budget=1200, lead_chunks=1)
    assert chunks[0] in selected and chunks[25] in selected


def test_single_oversized_chunk_is_still_returned():
    big = _chunk("a", 0, "word " * 5000)
    assert select_evidence([big, _chunk("a", 1, "tiny")], "word", budget=100) == [big]


class _FakeLLM:
    """Routes to `ask`, then answers citing the first chunk it was shown."""

    def __init__(self):
        self.qa_prompt = ""

    def generate(self, prompt, system_prompt=None, temperature=0.0):
        if "router for a research-paper assistant" in prompt:
            return json.dumps({"intent": "ask", "question": "How much energy was saved?"})
        self.qa_prompt = prompt
        ids = re.findall(r"^\[([^\]]+)\] Paper:", prompt, flags=re.MULTILINE)
        return json.dumps({"answer": "41 percent.", "evidence_ids": ids[:1], "evidence_sufficient": True})


def test_chat_ask_sends_only_relevant_chunks_within_budget(monkeypatch):
    monkeypatch.setenv("CHAT_EVIDENCE_CHAR_BUDGET", "3000")
    chunks = _filler("p1", 200)
    chunks[150] = _chunk("p1", 150, "The optimizer reduced training energy by 41 percent overall.")
    fake = _FakeLLM()
    app.dependency_overrides[get_llm_service] = lambda: fake
    try:
        response = TestClient(app).post(
            "/chat",
            json={
                "message": "How much energy was saved?",
                "library": [{"paper_id": "p1", "title": "Paper p1", "source": "upload"}],
                "evidence": [c.model_dump() for c in chunks],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["action"] == "ask"
    assert "p1-150" in fake.qa_prompt
    assert len(fake.qa_prompt) < 6000  # vs ~100k chars if all 200 chunks were sent
