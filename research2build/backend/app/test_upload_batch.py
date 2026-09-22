"""Tests for the /papers/upload-batch endpoint."""

import io
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

# tests/ (pdf_fixtures) sits outside backend/, which pytest's pythonpath covers
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))

client = TestClient(app)


def _pdf_bytes(pages: list[str]) -> bytes:
    from pdf_fixtures import make_pdf

    return make_pdf(pages)


def _upload(files: list[tuple[str, bytes]]):
    return client.post(
        "/papers/upload-batch",
        files=[
            ("files", (name, io.BytesIO(content), "application/pdf"))
            for name, content in files
        ],
    )


def test_upload_batch_returns_all_chunks_with_metadata():
    payload = [
        ("alpha.pdf", _pdf_bytes(["Introduction\nAlpha paper body text."])),
        ("beta.pdf", _pdf_bytes(["Results\nBeta paper body text."])),
    ]

    response = _upload(payload)

    assert response.status_code == 200
    chunks = response.json()
    assert len(chunks) >= 2
    assert {c["paper_title"] for c in chunks} == {"alpha", "beta"}
    assert all(c["section"] for c in chunks)
    assert all(c["page"] is not None for c in chunks)
    # Each paper gets its own paper_id
    assert len({c["paper_id"] for c in chunks}) == 2


def test_upload_batch_rejects_invalid_file_without_partial_ingest():
    payload = [
        ("good.pdf", _pdf_bytes(["Introduction\nSome text."])),
        ("bad.txt", (b"not a pdf")),
    ]

    response = _upload(payload)

    assert response.status_code == 422
    assert "bad.txt" in response.json()["detail"]


def test_upload_batch_rejects_empty_request():
    response = _upload([])
    assert response.status_code == 422


def _upload_single(name: str, content: bytes):
    return client.post(
        "/papers/upload",
        files={"file": (name, io.BytesIO(content), "application/pdf")},
    )


def test_reuploading_same_pdf_skips_reextraction_and_reembedding():
    """Same content -> same content-hash paper_id -> cached chunks returned
    without a second extraction or vector-store write (CLAUDE.md: process
    each paper once, never re-run extraction or embedding on every query)."""
    content = _pdf_bytes([f"Introduction\nRepeated upload body text {uuid.uuid4().hex}."])

    with patch("app.main.ingest_pdf", wraps=None) as mock_ingest:
        from app.ingestion import ingest_pdf as real_ingest_pdf

        mock_ingest.side_effect = real_ingest_pdf

        first = _upload_single("dup.pdf", content)
        assert first.status_code == 200
        assert mock_ingest.call_count == 1

        second = _upload_single("dup.pdf", content)
        assert second.status_code == 200
        assert mock_ingest.call_count == 1  # not called again — cache hit

    first_chunks = first.json()
    second_chunks = second.json()
    assert {c["paper_id"] for c in first_chunks} == {c["paper_id"] for c in second_chunks}
    assert first_chunks == second_chunks


def test_batch_upload_skips_reembedding_for_already_ingested_files():
    suffix = uuid.uuid4().hex
    fresh_content = _pdf_bytes([f"Introduction\nA freshly seen paper body {suffix}."])
    repeat_content = _pdf_bytes([f"Introduction\nRepeated upload body text {suffix}."])

    # Seed the cache for repeat_content via a prior single upload.
    seed = _upload_single("seed.pdf", repeat_content)
    assert seed.status_code == 200

    with patch("app.main.ingest_pdfs", wraps=None) as mock_ingest_pdfs:
        from app.ingestion import ingest_pdfs as real_ingest_pdfs

        mock_ingest_pdfs.side_effect = real_ingest_pdfs

        response = _upload([("fresh.pdf", fresh_content), ("repeat.pdf", repeat_content)])

    assert response.status_code == 200
    # ingest_pdfs should only have been asked to process the fresh file.
    ((processed_payloads,), _kwargs) = mock_ingest_pdfs.call_args
    assert [name for name, _ in processed_payloads] == ["fresh.pdf"]

    chunks = response.json()
    assert {c["paper_title"] for c in chunks} == {"fresh", "seed"}
