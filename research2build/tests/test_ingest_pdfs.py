import os
import tempfile
from unittest.mock import patch

import pytest

from backend.app.ingestion import IngestionError, extract_pages, ingest_pdfs
from backend.app.services import storage_service

from pdf_fixtures import make_pdf


def _batch_files(pages_lists: list[list[str]]) -> list[tuple[str, bytes]]:
    return [
        (f"paper-{i}.pdf", make_pdf(pages))
        for i, pages in enumerate(pages_lists)
    ]


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_service, "STORAGE_ROOT", tmp_path)
    return tmp_path


def test_ingest_pdfs_returns_chunks_per_paper_in_order(isolated_storage):
    files = _batch_files(
        [
            ["Introduction\nAlpha paper body text."],
            ["Methods\nBeta paper body text."],
            ["Results\nGamma paper body text."],
        ]
    )

    batches = ingest_pdfs(files, max_workers=1)

    assert len(batches) == 3
    assert [b[0].paper_title for b in batches] == ["paper-0", "paper-1", "paper-2"]
    assert {c.section for c in batches[0]} == {"Introduction"}
    assert {c.section for c in batches[1]} == {"Methods"}
    assert {c.section for c in batches[2]} == {"Results"}
    # One distinct paper_id per file
    assert len({b[0].paper_id for b in batches}) == 3


def test_ingest_pdfs_rejects_whole_batch_on_bad_file(isolated_storage):
    files = _batch_files([["Introduction\nGood paper."]])
    files.append(("notes.txt", b"not a pdf"))

    with pytest.raises(storage_service.InvalidUploadError, match="notes.txt"):
        ingest_pdfs(files, max_workers=1)

    # Nothing was persisted before the failure
    assert list(isolated_storage.iterdir()) == []


def test_ingest_pdfs_preserves_section_page_metadata(isolated_storage):
    files = _batch_files(
        [
            [
                "Introduction\nThis paper studies latency in distributed systems.",
                "Limitations\nOur evaluation only covers a single datacenter.",
            ]
        ]
    )

    batches = ingest_pdfs(files, max_workers=1)

    chunks = batches[0]
    assert {c.section for c in chunks} == {"Introduction", "Limitations"}
    assert all(c.page is not None for c in chunks)
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_parallel_ingest_matches_sequential_results(isolated_storage):
    """Parallel extraction (the multi-PDF path) must produce identical
    chunks to sequential extraction — parallelism must not drop or
    reorder evidence."""
    files = _batch_files(
        [
            ["Introduction\nAlpha paper text."],
            ["Results\nBeta paper text."],
            ["Conclusion\nGamma paper text."],
        ]
    )

    sequential = ingest_pdfs(files, max_workers=1)
    parallel = ingest_pdfs(files)

    assert len(parallel) == len(sequential) == 3
    for seq_batch, par_batch in zip(sequential, parallel):
        assert len(par_batch) == len(seq_batch)
        for seq_chunk, par_chunk in zip(seq_batch, par_batch):
            assert seq_chunk.text == par_chunk.text
            assert seq_chunk.section == par_chunk.section
            assert seq_chunk.page == par_chunk.page
            # paper ids differ (fresh uuid per ingest run), the rest matches


def test_extract_pages_pymupdf_matches_pypdf_page_numbers(isolated_storage):
    pdf_bytes = make_pdf(["Introduction\nPage one text.", "Results\nPage two text."])
    pages = extract_pages(pdf_bytes)

    assert [p.number for p in pages] == [1, 2]
    assert "Page one text" in pages[0].text
    assert "Page two text" in pages[1].text


def test_extract_pages_raises_ingestion_error_on_garbage():
    from backend.app.ingestion import extract_pages as _ep

    with pytest.raises(IngestionError):
        _ep(b"this is not a pdf at all")
