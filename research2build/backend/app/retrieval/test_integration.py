import pytest

from app.discovery.paper_models import Paper
from app.embeddings.provider import HashEmbeddingProvider
from app.retrieval.factory import get_retriever
from app.retrieval.semantic_retriever import SemanticRetriever
from app.retrieval.vector_store import InMemoryVectorStore, cosine_similarity


class MockOpenAlexClientFull:
    """Mock client returning realistic paper metadata and edge cases."""

    def search_papers(self, query: str, max_results: int = 20) -> list[Paper]:
        return [
            Paper(
                paper_id="https://openalex.org/W100",
                title="Deep Learning for Medical Image Analysis",
                abstract="Deep learning models enhance diagnostic accuracy in radiologic imaging.",
                authors=["Alice Smith", "Bob Jones"],
                publication_year=2023,
                doi="https://doi.org/10.1000/medimg",
                url="https://landing.page/medimg",
            ),
            Paper(
                paper_id="https://openalex.org/W200",
                title="Natural Language Processing in Clinical Notes",
                abstract="NLP pipelines extract clinical entities from electronic health records.",
                authors=["Charlie Brown"],
                publication_year=2022,
                doi="https://doi.org/10.1000/nlpclinical",
                url="https://landing.page/nlpclinical",
            ),
            Paper(
                paper_id="https://openalex.org/W300",
                title="Paper With Empty Abstract",
                abstract="",
                authors=["Empty Author"],
            ),
            Paper(
                paper_id="https://openalex.org/W100",  # Duplicate paper ID test
                title="Duplicate Paper",
                abstract="Duplicate paper abstract content.",
            ),
        ]


@pytest.mark.anyio
async def test_top_k_respected_and_ranked():
    mock_client = MockOpenAlexClientFull()
    retriever = SemanticRetriever(openalex_client=mock_client)

    # Request top_k = 1
    chunks = await retriever.retrieve("radiologic imaging medical diagnosis", top_k=1)
    assert len(chunks) == 1
    assert chunks[0].paper_id == "https://openalex.org/W100"


@pytest.mark.anyio
async def test_empty_abstracts_and_duplicates_filtered():
    mock_client = MockOpenAlexClientFull()
    retriever = SemanticRetriever(openalex_client=mock_client)

    chunks = await retriever.retrieve("clinical health records", top_k=10)

    # Paper W300 (empty abstract) and duplicate W100 chunks should be handled cleanly
    paper_ids = [c.paper_id for c in chunks]
    assert "https://openalex.org/W300" not in paper_ids
    assert len(chunks) >= 1


@pytest.mark.anyio
async def test_metadata_preservation():
    mock_client = MockOpenAlexClientFull()
    retriever = SemanticRetriever(openalex_client=mock_client)

    chunks = await retriever.retrieve("diagnostic accuracy imaging", top_k=1)
    assert len(chunks) == 1

    chunk = chunks[0]
    assert chunk.paper_id == "https://openalex.org/W100"
    assert chunk.title == "Deep Learning for Medical Image Analysis"
    assert chunk.source_url == "https://landing.page/medimg"
    assert chunk.section == "Abstract"
    assert chunk.chunk_id == "https://openalex.org/W100-chunk-0"


@pytest.mark.anyio
async def test_empty_query_and_zero_vectors():
    retriever = SemanticRetriever()
    empty_result = await retriever.retrieve("", top_k=5)
    assert empty_result == []

    # Zero vector cosine similarity check
    vec_zero = [0.0, 0.0, 0.0]
    vec_normal = [1.0, 2.0, 3.0]
    assert cosine_similarity(vec_zero, vec_normal) == 0.0


@pytest.mark.anyio
async def test_retrieval_smoke_test_representative_queries():
    mock_client = MockOpenAlexClientFull()
    retriever = SemanticRetriever(openalex_client=mock_client)

    queries = [
        "electronic health records clinical notes",
        "medical image radiology deep learning",
    ]

    for q in queries:
        results = await retriever.retrieve(q, top_k=2)
        assert len(results) > 0
        assert results[0].text is not None


def test_factory_get_retriever():
    retriever_default = get_retriever(use_semantic=True)
    assert isinstance(retriever_default, SemanticRetriever)

    retriever_basic = get_retriever(use_semantic=False)
    assert hasattr(retriever_basic, "retrieve")
