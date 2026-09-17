"""End-to-end integration tests for Member 5 work item 4.

Exercises the full pipeline purely through the HTTP API: two paper
analyses -> comparison -> recurring-limitation-derived opportunities ->
project proposals -> feasibility scoring -> PRD generation. Also covers
the OpenAlex-backed discovery route with the network call mocked out.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.discovery.paper_models import Paper
from backend.app.main import app

client = TestClient(app)


def _analysis(paper_id: str, paper_title: str, limitation_text: str) -> dict:
    return {
        "paper_id": paper_id,
        "paper_title": paper_title,
        "problem": None,
        "objective": None,
        "methodology": None,
        "dataset": None,
        "models": None,
        "results": [],
        "limitations": [
            {
                "claim": limitation_text,
                "citations": [
                    {
                        "chunk_id": f"{paper_id}-c1",
                        "paper_id": paper_id,
                        "paper_title": paper_title,
                        "section": "Limitations",
                        "page": 9,
                        "quote": limitation_text,
                    }
                ],
            }
        ],
        "future_work": [],
    }


def test_discovery_search_maps_openalex_results():
    fake_papers = [
        Paper(
            paper_id="https://openalex.org/W1",
            title="Federated Learning at Scale",
            abstract="A survey of communication-efficient federated learning.",
            authors=["A. Ricci"],
            publication_year=2023,
            url="https://openalex.org/W1",
        )
    ]

    with patch(
        "backend.app.main.OpenAlexClient.search_papers",
        return_value=fake_papers,
    ):
        response = client.post(
            "/discovery/search",
            json={"query": "federated learning", "max_results": 5},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["paper_id"] == "https://openalex.org/W1"
    assert data[0]["year"] == 2023


def test_discovery_search_rejects_empty_query():
    response = client.post("/discovery/search", json={"query": "   "})
    assert response.status_code == 400


def test_full_pipeline_through_http_api():
    # Two analyses sharing a recurring limitation.
    analyses = [
        _analysis("p1", "Federated Learning at Scale", "Evaluation only covers a single datacenter."),
        _analysis("p2", "Edge Inference Survey", "Evaluation only covers a single datacenter."),
    ]

    compare_resp = client.post("/research-intelligence/compare", json={"analyses": analyses})
    assert compare_resp.status_code == 200
    comparison = compare_resp.json()
    assert set(comparison["paper_ids"]) == {"p1", "p2"}

    opp_resp = client.post("/research-intelligence/opportunities", json={"analyses": analyses})
    assert opp_resp.status_code == 200
    opportunities = opp_resp.json()
    assert len(opportunities) >= 1
    assert all(o["novelty_confidence"] == "Requires human validation" for o in opportunities)

    proposals_resp = client.post(
        "/research-intelligence/proposals",
        json={"opportunities": opportunities},
    )
    assert proposals_resp.status_code == 200
    proposals = proposals_resp.json()
    assert 3 <= len(proposals) <= 5
    proposal = proposals[0]
    assert proposal["novelty_confidence"] == "Requires human validation"

    feasibility_resp = client.post(
        "/feasibility/score",
        json={
            "proposal": proposal,
            "constraints": {
                "team_size": 2,
                "weeks_available": 8,
                "budget_usd": 50,
                "skills": ["Python"],
            },
        },
    )
    assert feasibility_resp.status_code == 200
    assessment = feasibility_resp.json()
    assert assessment["proposal_id"] == proposal["proposal_id"]
    assert 0 <= assessment["score"] <= 100
    assert len(assessment["roadmap"]["milestones"]) == 7

    prd_resp = client.post(
        "/deliverables/prd",
        json={"proposal": proposal, "feasibility": assessment},
    )
    assert prd_resp.status_code == 200
    prd = prd_resp.json()
    assert prd["proposal_id"] == proposal["proposal_id"]
    assert prd["novelty_confidence"] == "Requires human validation"
    assert str(assessment["score"]) in prd["feasibility_summary"]


def test_compare_requires_at_least_two_analyses():
    analyses = [_analysis("p1", "Solo Paper", "Small sample size.")]
    response = client.post("/research-intelligence/compare", json={"analyses": analyses})
    assert response.status_code == 422
