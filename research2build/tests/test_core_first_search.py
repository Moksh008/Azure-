"""Chat paper search goes through CORE, falling back to OpenAlex."""

import json

import requests
from fastapi.testclient import TestClient

from backend.app.discovery.core_client import CoreClient
from backend.app.discovery.multi_source import search_core_first
from backend.app.discovery.openalex_client import OpenAlexClient
from backend.app.discovery.paper_models import Paper
from backend.app.main import app
from backend.app.services.llm_factory import get_llm_service


def _paper(paper_id: str, title: str) -> Paper:
    return Paper(paper_id=paper_id, title=title, abstract="abs", pdf_url=f"https://x/{paper_id}.pdf")


def test_uses_core_when_configured(monkeypatch):
    monkeypatch.setenv("CORE_API_KEY", "k")
    monkeypatch.setattr(CoreClient, "search_papers", lambda self, q, max_results=20: [_paper("core:1", "From CORE")])
    monkeypatch.setattr(OpenAlexClient, "search_papers", lambda *a, **k: (_ for _ in ()).throw(AssertionError("OpenAlex must not be called")))

    papers, source = search_core_first("anything", 5)

    assert source == "CORE"
    assert [p.paper_id for p in papers] == ["core:1"]


def test_duplicate_repository_copies_are_merged_keeping_the_pdf_link(monkeypatch):
    monkeypatch.setenv("CORE_API_KEY", "k")
    no_pdf = Paper(paper_id="core:1", title="DuetRAG: Collaborative RAG", abstract="abs")
    with_pdf = Paper(paper_id="core:2", title="DuetRAG:  Collaborative RAG", abstract="abs", pdf_url="https://x/2.pdf")
    other = _paper("core:3", "A different paper")
    monkeypatch.setattr(CoreClient, "search_papers", lambda self, q, max_results=20: [no_pdf, with_pdf, other])

    papers, _ = search_core_first("anything", 5)

    assert [p.paper_id for p in papers] == ["core:1", "core:3"]
    assert papers[0].pdf_url == "https://x/2.pdf"


def test_falls_back_to_openalex_when_core_errors(monkeypatch):
    monkeypatch.setenv("CORE_API_KEY", "k")

    def boom(self, q, max_results=20):
        raise requests.HTTPError("429 rate limited")

    monkeypatch.setattr(CoreClient, "search_papers", boom)
    monkeypatch.setattr(OpenAlexClient, "search_papers", lambda self, q, max_results=20: [_paper("https://openalex.org/W1", "From OA")])

    papers, source = search_core_first("anything", 5)

    assert source == "OpenAlex"
    assert papers[0].title == "From OA"


def test_falls_back_to_openalex_when_core_finds_nothing(monkeypatch):
    monkeypatch.setenv("CORE_API_KEY", "k")
    monkeypatch.setattr(CoreClient, "search_papers", lambda self, q, max_results=20: [])
    monkeypatch.setattr(OpenAlexClient, "search_papers", lambda self, q, max_results=20: [_paper("https://openalex.org/W1", "From OA")])

    _, source = search_core_first("anything", 5)

    assert source == "OpenAlex"


def test_uses_openalex_when_no_core_key(monkeypatch):
    monkeypatch.delenv("CORE_API_KEY", raising=False)
    monkeypatch.setattr(OpenAlexClient, "search_papers", lambda self, q, max_results=20: [_paper("https://openalex.org/W1", "From OA")])

    _, source = search_core_first("anything", 5)

    assert source == "OpenAlex"


class _SearchRouterLLM:
    def generate(self, prompt, system_prompt=None, temperature=0.0):
        return json.dumps({"intent": "search", "query": "graph neural networks"})


def test_chat_search_reply_says_it_used_core(monkeypatch):
    monkeypatch.setenv("CORE_API_KEY", "k")
    monkeypatch.setattr(CoreClient, "search_papers", lambda self, q, max_results=20: [_paper("core:7", "GNN paper")])
    app.dependency_overrides[get_llm_service] = lambda: _SearchRouterLLM()
    try:
        response = TestClient(app).post("/chat", json={"message": "find papers on graph neural networks"})
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["action"] == "search"
    assert "via CORE" in body["reply"]
    assert body["discovered_papers"][0]["paper_id"] == "core:7"
    assert body["discovered_papers"][0]["pdf_url"] == "https://x/core:7.pdf"
