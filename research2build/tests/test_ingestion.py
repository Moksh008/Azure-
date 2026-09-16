import pytest

from backend.app.ingestion import IngestionError, extract_pages, ingest_pdf
from backend.app.services import storage_service
from backend.app.services.chunking_service import PageText, chunk_pages
from backend.app.services.storage_service import InvalidUploadError, validate_pdf_upload
from backend.app.services.text_service import detect_heading, normalize_text

from pdf_fixtures import make_pdf


# --- text_service -----------------------------------------------------


def test_normalize_text_rejoins_hyphenated_words():
    assert normalize_text("this is an exam-\nple sentence") == "this is an example sentence"


def test_normalize_text_folds_soft_linebreaks_but_keeps_paragraphs():
    raw = "First line\nstill first paragraph.\n\nSecond paragraph starts here."
    assert normalize_text(raw) == "First line still first paragraph.\n\nSecond paragraph starts here."


@pytest.mark.parametrize(
    "line,expected",
    [
        ("Introduction", "Introduction"),
        ("INTRODUCTION", "Introduction"),
        ("1. Introduction", "Introduction"),
        ("2.3 Related Work", "Related Work"),
        ("Limitations", "Limitations"),
        ("This is just a regular sentence.", None),
        ("", None),
    ],
)
def test_detect_heading(line, expected):
    assert detect_heading(line) == expected


# --- chunking_service ---------------------------------------------------


def test_chunk_pages_tags_section_and_page():
    pages = [
        PageText(number=1, text="Introduction\nSome background text about the problem."),
        PageText(number=2, text="Results\nWe observed a strong effect in our experiments."),
    ]
    chunks = chunk_pages(pages, paper_id="paper1", paper_title="Test Paper")

    assert [c.section for c in chunks] == ["Introduction", "Results"]
    assert [c.page for c in chunks] == [1, 2]
    assert all(c.paper_id == "paper1" for c in chunks)
    assert all(c.chunk_id.startswith("paper1-") for c in chunks)
    assert "background" in chunks[0].text.lower()


def test_chunk_pages_splits_long_sections_with_overlap():
    long_text = "Method\n" + " ".join(f"sentence{i}" for i in range(400))
    pages = [PageText(number=1, text=long_text)]

    chunks = chunk_pages(pages, paper_id="paper1", paper_title="Test", chunk_size=500, overlap=50)

    assert len(chunks) > 1
    assert all(c.section == "Method" for c in chunks)
    # overlap: the tail of one chunk should reappear at the start of the next
    tail = chunks[0].text[-30:]
    assert tail in chunks[1].text


# --- storage_service ------------------------------------------------------


def test_validate_pdf_upload_rejects_non_pdf():
    with pytest.raises(InvalidUploadError):
        validate_pdf_upload("notes.txt", b"hello")


def test_validate_pdf_upload_rejects_empty():
    with pytest.raises(InvalidUploadError):
        validate_pdf_upload("paper.pdf", b"")


def test_validate_pdf_upload_rejects_fake_pdf_content():
    with pytest.raises(InvalidUploadError):
        validate_pdf_upload("paper.pdf", b"not actually a pdf")


def test_validate_pdf_upload_accepts_real_pdf():
    pdf_bytes = make_pdf(["Abstract\nSome text."])
    validate_pdf_upload("paper.pdf", pdf_bytes)  # should not raise


# --- ingestion (end to end) -----------------------------------------------


def test_extract_pages_preserves_page_numbers():
    pdf_bytes = make_pdf(["Introduction\nPage one text.", "Results\nPage two text."])
    pages = extract_pages(pdf_bytes)

    assert [p.number for p in pages] == [1, 2]
    assert "Page one text" in pages[0].text
    assert "Page two text" in pages[1].text


def test_ingest_pdf_produces_evidence_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_service, "STORAGE_ROOT", tmp_path)

    pdf_bytes = make_pdf(
        [
            "Introduction\nThis paper studies latency in distributed systems.",
            "Limitations\nOur evaluation only covers a single datacenter.",
        ]
    )

    chunks = ingest_pdf("latency-paper.pdf", pdf_bytes)

    assert len(chunks) >= 2
    assert {c.section for c in chunks} == {"Introduction", "Limitations"}
    assert all(c.paper_title == "latency-paper" for c in chunks)
    assert all(c.paper_id for c in chunks)
    assert len({c.paper_id for c in chunks}) == 1  # one paper_id per paper
    assert len({c.chunk_id for c in chunks}) == len(chunks)  # unique chunk ids

    stored = storage_service.paper_pdf_path(chunks[0].paper_id)
    assert stored.exists()


def test_ingest_pdf_rejects_invalid_upload(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_service, "STORAGE_ROOT", tmp_path)

    with pytest.raises(InvalidUploadError):
        ingest_pdf("notes.txt", b"hello")
