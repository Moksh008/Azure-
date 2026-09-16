from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.retrieval.evidence import EvidenceChunk

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "research2build-api"}


@patch("app.main.get_retriever")
def test_retrieval_search_endpoint_success(mock_get_retriever):
    mock_retriever = AsyncMock()
    mock_retriever.retrieve.return_value = [
        EvidenceChunk(
            chunk_id="chunk-101",
            paper_id="paper-101",
            title="Machine Learning in Medicine",
            text="AI models detect early markers of cardiac disease.",
            source_url="https://doi.org/10.1000/med",
            section="Abstract",
        )
    ]
    mock_get_retriever.return_value = mock_retriever

    response = client.post(
        "/retrieval/search",
        json={"query": "cardiac disease detection", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert "chunks" in data
    assert len(data["chunks"]) == 1
    assert data["chunks"][0]["chunk_id"] == "chunk-101"
    assert data["chunks"][0]["paper_title"] == "Machine Learning in Medicine"


def test_retrieval_search_validation_empty_query():
    response = client.post(
        "/retrieval/search",
        json={"query": "   ", "top_k": 5},
    )
    assert response.status_code == 400
    assert "Query string must not be empty" in response.json()["detail"]


def test_retrieval_search_validation_invalid_top_k():
    response = client.post(
        "/retrieval/search",
        json={"query": "test query", "top_k": 0},
    )
    assert response.status_code == 422  # Pydantic validation error
