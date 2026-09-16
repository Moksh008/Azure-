import pytest

from app.discovery.paper_models import Paper
from app.retrieval.semantic_retriever import SemanticRetriever


class MockOpenAlexClient:
    def search_papers(self, query: str, max_results: int = 20) -> list[Paper]:
        return [
            Paper(
                paper_id="W001",
                title="AI in Cardiology",
                abstract="Machine learning and neural networks detect cardiac arrhythmia accurately.",
            ),
            Paper(
                paper_id="W002",
                title="Deep Learning in Oncology",
                abstract="Deep convolutional networks classify skin cancer lesions with high precision.",
            ),
        ]


@pytest.mark.anyio
async def test_semantic_retriever():
    mock_client = MockOpenAlexClient()
    retriever = SemanticRetriever(openalex_client=mock_client)

    chunks = await retriever.retrieve("cardiac arrhythmia detection", top_k=2)

    assert len(chunks) == 2
    assert chunks[0].paper_id == "W001"
    assert "arrhythmia" in chunks[0].text
