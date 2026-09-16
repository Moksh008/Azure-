import pytest

from backend.app.services.citation_service import (
    UngroundedClaimError,
    cite_chunk,
    cite_chunks,
    make_grounded_claim,
)
from shared.schemas import EvidenceChunk


def _chunk(chunk_id: str, text: str, section: str = "Limitations", page: int = 3) -> EvidenceChunk:
    return EvidenceChunk(
        chunk_id=chunk_id,
        paper_id="abc123",
        paper_title="A Study of Latency",
        section=section,
        page=page,
        text=text,
    )


def test_cite_chunk_defaults_quote_to_full_text():
    chunk = _chunk("abc123-0001", "Our evaluation only covers a single datacenter.")
    citation = cite_chunk(chunk)

    assert citation.chunk_id == chunk.chunk_id
    assert citation.quote == chunk.text


def test_cite_chunks_pairs_quotes_positionally():
    chunks = [
        _chunk("abc123-0001", "Latency was the main bottleneck."),
        _chunk("abc123-0002", "Throughput was acceptable."),
    ]

    citations = cite_chunks(chunks, quotes=["main bottleneck", None])

    assert citations[0].quote == "main bottleneck"
    assert citations[1].quote == chunks[1].text


def test_cite_chunks_rejects_mismatched_quote_length():
    chunks = [_chunk("abc123-0001", "text")]

    with pytest.raises(ValueError):
        cite_chunks(chunks, quotes=["a", "b"])


def test_make_grounded_claim_attaches_citations():
    chunk = _chunk("abc123-0001", "Our evaluation only covers a single datacenter.")

    grounded = make_grounded_claim(
        "The paper's evaluation is limited to one datacenter.",
        [chunk],
        quotes=["single datacenter"],
    )

    assert grounded.claim == "The paper's evaluation is limited to one datacenter."
    assert len(grounded.citations) == 1
    assert grounded.citations[0].quote == "single datacenter"


def test_make_grounded_claim_rejects_empty_chunks():
    with pytest.raises(UngroundedClaimError):
        make_grounded_claim("An ungrounded claim.", [])
