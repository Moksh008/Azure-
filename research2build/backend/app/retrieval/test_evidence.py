from app.retrieval.evidence import EvidenceChunk


def test_evidence_chunk():
    chunk = EvidenceChunk(
        chunk_id="demo-001",
        paper_id="https://openalex.org/W123456789",
        title="Fake News Detection on Social Media",
        text="Social media enables rapid dissemination of news and misinformation.",
        source_url="https://doi.org/10.1145/3137597.3137600",
        page_number=1,
        section="Introduction",
    )
    assert chunk.chunk_id == "demo-001"
    assert chunk.paper_id == "https://openalex.org/W123456789"
    assert chunk.title == "Fake News Detection on Social Media"
    assert chunk.section == "Introduction"


def main():
    chunk = EvidenceChunk(
        chunk_id="demo-001",
        paper_id="https://openalex.org/W123456789",
        title="Fake News Detection on Social Media",
        text="Social media enables rapid dissemination of news and misinformation.",
        source_url="https://doi.org/10.1145/3137597.3137600",
        page_number=1,
        section="Introduction",
    )

    print(chunk)


if __name__ == "__main__":
    main()
