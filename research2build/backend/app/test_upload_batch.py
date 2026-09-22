"""Tests for the /papers/upload-batch endpoint."""

import io
import sys
from pathlib import Path

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
