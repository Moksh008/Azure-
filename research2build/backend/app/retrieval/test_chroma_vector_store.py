"""Tests for the ChromaDB-backed vector store.

Uses real ChromaDB against a throwaway temp directory (via conftest's
CHROMA_PATH), so persistence semantics are exercised for real without
touching the repo's ./chroma_db.
"""

import uuid

from app.embeddings.provider import HashEmbeddingProvider
from app.retrieval.chroma_vector_store import (
    DISCOVERY_COLLECTION,
    LIBRARY_COLLECTION,
    ChromaVectorStore,
)
from app.retrieval.evidence import EvidenceChunk


def _make_store(collection: str = LIBRARY_COLLECTION) -> ChromaVectorStore:
    # Unique path per store keeps tests isolated from each other.
    import os
    import tempfile

    return ChromaVectorStore(
        path=tempfile.mkdtemp(prefix=f"r2b-chroma-{collection}-"),
        collection_name=collection,
        embedding_provider=HashEmbeddingProvider(),
    )


def _chunk(chunk_id: str, text: str, **overrides) -> EvidenceChunk:
    defaults = dict(
        chunk_id=chunk_id,
        paper_id="paper-1",
        title="Test Paper",
        text=text,
        source_url=None,
        page_number=None,
        section=None,
    )
    defaults.update(overrides)
    return EvidenceChunk(**defaults)


def test_add_and_search_roundtrips_citation_metadata():
    store = _make_store()
    chunk = _chunk(
        f"p1-0001-{uuid.uuid4().hex[:8]}",
        "Gradient descent converges faster with adaptive learning rates.",
        paper_id="paper-1",
        title="Optimization Deep Dive",
        source_url="https://example.org/paper-1",
        page_number=4,
        section="Results",
    )

    store.add_chunks([chunk])
    results = store.search("adaptive learning rate optimization", top_k=1)

    assert len(results) == 1
    got = results[0]
    assert got.chunk_id == chunk.chunk_id
    assert got.paper_id == "paper-1"
    assert got.title == "Optimization Deep Dive"
    assert got.source_url == "https://example.org/paper-1"
    assert got.page_number == 4
    assert got.section == "Results"
    assert got.text == chunk.text


def test_none_metadata_fields_survive_roundtrip():
    store = _make_store()
    chunk = _chunk(f"p1-0002-{uuid.uuid4().hex[:8]}", "Some abstract-like text.")

    store.add_chunks([chunk])
    got = store.search("abstract-like text", top_k=1)[0]

    assert got.source_url is None
    assert got.page_number is None
    assert got.section is None


def test_upsert_same_id_replaces_document():
    store = _make_store()
    chunk_id = f"p1-0003-{uuid.uuid4().hex[:8]}"
    store.add_chunks([_chunk(chunk_id, "original text")])
    store.add_chunks([_chunk(chunk_id, "revised text")])

    assert len(store) == 1
    got = store.search("revised text", top_k=1)[0]
    assert got.text == "revised text"


def test_clear_removes_all_chunks():
    store = _make_store()
    store.add_chunks(
        [
            _chunk(f"p1-0004-{uuid.uuid4().hex[:8]}", "alpha beta gamma"),
            _chunk(f"p1-0005-{uuid.uuid4().hex[:8]}", "delta epsilon zeta"),
        ]
    )
    assert len(store) == 2

    store.clear()
    assert len(store) == 0
    assert store.search("alpha beta gamma", top_k=5) == []


def test_collections_are_independent():
    library = _make_store(LIBRARY_COLLECTION)
    discovery = _make_store(DISCOVERY_COLLECTION)

    library.add_chunks([_chunk("lib-1", "full text evidence from an uploaded pdf")])
    # Same clear() SemanticRetriever calls on every retrieve()
    discovery.clear()
    discovery.add_chunks([_chunk("disc-1", "openalex abstract snippet")])

    assert len(library) == 1
    assert len(discovery) == 1
    assert library.search("uploaded pdf", top_k=1)[0].chunk_id == "lib-1"


def test_empty_query_returns_nothing():
    store = _make_store()
    assert store.search("", top_k=3) == []
    assert store.search("   ", top_k=3) == []


def test_add_chunks_vector_count_mismatch_raises():
    store = _make_store()
    chunks = [_chunk("p1-0006", "text one"), _chunk("p1-0007", "text two")]
    try:
        store.add_chunks(chunks, vectors=[[0.1, 0.2]])
    except ValueError as exc:
        assert "must match" in str(exc)
    else:
        raise AssertionError("Expected ValueError for vector count mismatch")
