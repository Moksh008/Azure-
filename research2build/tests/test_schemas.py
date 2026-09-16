from shared.schemas import Citation, EvidenceChunk


def _sample_chunk() -> EvidenceChunk:
    return EvidenceChunk(
        chunk_id="abc123-0001",
        paper_id="abc123",
        paper_title="A Study of Latency",
        section="Limitations",
        page=7,
        text="Our evaluation only covers a single datacenter.",
    )


def test_citation_from_chunk_defaults_quote_to_full_text():
    chunk = _sample_chunk()
    citation = Citation.from_chunk(chunk)

    assert citation.chunk_id == chunk.chunk_id
    assert citation.paper_id == chunk.paper_id
    assert citation.paper_title == chunk.paper_title
    assert citation.section == chunk.section
    assert citation.page == chunk.page
    assert citation.quote == chunk.text


def test_citation_from_chunk_accepts_explicit_quote():
    chunk = _sample_chunk()
    citation = Citation.from_chunk(chunk, quote="single datacenter")

    assert citation.quote == "single datacenter"
    assert citation.chunk_id == chunk.chunk_id
