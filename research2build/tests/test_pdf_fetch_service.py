"""download_pdf retries once on transient network errors, never on permanent ones."""

import pytest
import requests

from backend.app.services import pdf_fetch_service
from backend.app.services.pdf_fetch_service import PdfDownloadError, download_pdf


class _Response:
    def __init__(self, body=b"%PDF-1.4 ok", status=200, headers=None):
        self._body, self.status_code, self.headers = body, status, headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def iter_content(self, chunk_size):
        yield self._body


def _script(monkeypatch, outcomes):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        outcome = outcomes[min(len(calls), len(outcomes)) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(pdf_fetch_service.requests, "get", fake_get)
    return calls


def test_retries_once_after_a_timeout(monkeypatch):
    calls = _script(monkeypatch, [requests.ReadTimeout("slow"), _Response()])
    assert download_pdf("https://x/a.pdf") == b"%PDF-1.4 ok"
    assert len(calls) == 2


def test_retries_once_after_a_dropped_connection(monkeypatch):
    calls = _script(monkeypatch, [requests.ConnectionError("reset"), _Response()])
    assert download_pdf("https://x/a.pdf") == b"%PDF-1.4 ok"
    assert len(calls) == 2


def test_gives_up_after_the_second_timeout(monkeypatch):
    calls = _script(monkeypatch, [requests.ReadTimeout("slow")])
    with pytest.raises(PdfDownloadError):
        download_pdf("https://x/a.pdf")
    assert len(calls) == 2


def test_does_not_retry_a_404(monkeypatch):
    calls = _script(monkeypatch, [_Response(status=404)])
    with pytest.raises(PdfDownloadError):
        download_pdf("https://x/a.pdf")
    assert len(calls) == 1


def test_does_not_retry_an_oversized_file(monkeypatch):
    too_big = str(pdf_fetch_service.MAX_FETCHED_PDF_BYTES + 1)
    calls = _script(monkeypatch, [_Response(headers={"Content-Length": too_big})])
    with pytest.raises(PdfDownloadError, match="larger than"):
        download_pdf("https://x/a.pdf")
    assert len(calls) == 1
