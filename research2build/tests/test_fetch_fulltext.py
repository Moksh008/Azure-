"""Tests for the /papers/fetch-fulltext endpoint.

Regression coverage for a real bug: paper_id_override (an OpenAlex URL
like "https://openalex.org/W123", containing "/" and ":") was being used
directly as the local storage filename, which breaks on every platform
(and especially on Windows, where ":" is invalid in a path) — every
full-text fetch for a discovered paper failed with an OSError before
ever reaching the LLM/embedding pipeline.
"""

import io
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

sys.path.insert(0, str(Path(__file__).resolve().parent))

client = TestClient(app)


def _pdf_bytes(pages: list[str]) -> bytes:
    from pdf_fixtures import make_pdf

    return make_pdf(pages)


def test_fetch_fulltext_handles_openalex_style_paper_id_with_unsafe_path_chars():
    content = _pdf_bytes(["Introduction\nFull text body for a discovered paper."])

    with patch("app.main.download_pdf", return_value=content):
        response = client.post(
            "/papers/fetch-fulltext",
            json={
                "paper_id": "https://openalex.org/W4402671659",
                "title": "LLM in a flash",
                "pdf_url": "https://example.com/paper.pdf",
            },
        )

    assert response.status_code == 200, response.text
    chunks = response.json()
    assert len(chunks) > 0
    assert all(c["paper_id"] == "https://openalex.org/W4402671659" for c in chunks)
