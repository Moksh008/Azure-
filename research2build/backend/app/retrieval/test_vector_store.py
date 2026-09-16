from app.embeddings.provider import HashEmbeddingProvider
from app.retrieval.evidence import EvidenceChunk
from app.retrieval.vector_store import InMemoryVectorStore, cosine_similarity


def test_cosine_similarity():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    vec_c = [0.0, 1.0, 0.0]

    assert abs(cosine_similarity(vec_a, vec_b) - 1.0) < 1e-5
    assert abs(cosine_similarity(vec_a, vec_c) - 0.0) < 1e-5


def test_in_memory_vector_store():
    store = InMemoryVectorStore(embedding_provider=HashEmbeddingProvider())

    chunk1 = EvidenceChunk(
        chunk_id="chunk-1",
        paper_id="paper-1",
        title="Healthcare ML",
        text="Machine learning models improve disease diagnosis in healthcare.",
    )
    chunk2 = EvidenceChunk(
        chunk_id="chunk-2",
        paper_id="paper-2",
        title="Astrophysics",
        text="Black holes emit Hawking radiation and warp spacetime.",
    )

    store.add_chunks([chunk1, chunk2])
    assert len(store) == 2

    results = store.search("diagnosis of disease in healthcare", top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
