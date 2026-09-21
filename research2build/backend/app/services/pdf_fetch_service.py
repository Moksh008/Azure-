"""Download a remote PDF (e.g. an open-access copy found via OpenAlex).

Publisher CDNs commonly throttle or block the default `python-requests`
User-Agent, so requests here identify as a normal browser. Downloads are
streamed and aborted as soon as they exceed the upload size limit, so a
huge file is never fully pulled just to be rejected afterwards.
"""

from __future__ import annotations

import time

import requests

from .storage_service import MAX_FETCHED_PDF_BYTES

CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 30
TOTAL_DEADLINE_SECONDS = 90

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*;q=0.8",
}


class PdfDownloadError(Exception):
    """Raised when a remote PDF can't be downloaded within our limits."""


class _TransientDownloadError(PdfDownloadError):
    """A timeout / dropped connection — worth one more try, unlike a 404 or
    an oversized file, which would fail the same way again."""


def download_pdf(url: str) -> bytes:
    try:
        return _download_once(url)
    except _TransientDownloadError:
        return _download_once(url)


def _download_once(url: str) -> bytes:
    limit_mb = MAX_FETCHED_PDF_BYTES // (1024 * 1024)
    too_large = PdfDownloadError(f"PDF is larger than the {limit_mb}MB limit.")

    try:
        with requests.get(
            url,
            headers=BROWSER_HEADERS,
            timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
            stream=True,
        ) as response:
            response.raise_for_status()

            declared = response.headers.get("Content-Length")
            if declared and declared.isdigit() and int(declared) > MAX_FETCHED_PDF_BYTES:
                raise too_large

            deadline = time.monotonic() + TOTAL_DEADLINE_SECONDS
            parts: list[bytes] = []
            total = 0
            for part in response.iter_content(chunk_size=64 * 1024):
                total += len(part)
                if total > MAX_FETCHED_PDF_BYTES:
                    raise too_large
                if time.monotonic() > deadline:
                    raise PdfDownloadError(
                        f"Download took longer than {TOTAL_DEADLINE_SECONDS}s."
                    )
                parts.append(part)
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise _TransientDownloadError(str(exc)) from exc
    except requests.RequestException as exc:
        raise PdfDownloadError(str(exc)) from exc

    return b"".join(parts)
