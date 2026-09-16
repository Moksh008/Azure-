"""PDF -> text -> EvidenceChunk pipeline.

Upload validation and local storage: services/storage_service.py
Text normalization and heading detection: services/text_service.py
Chunk assembly: services/chunking_service.py

This module wires those pieces together into a single `ingest_pdf` entry
point used by the API layer.
"""

from __future__ import annotations

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from shared.schemas import EvidenceChunk

from .services import storage_service
from .services.chunking_service import PageText, chunk_pages
from .services.text_service import detect_heading, normalize_text


class IngestionError(ValueError):
    """Raised when a PDF can't be validated or parsed into evidence."""


def _isolate_headings(raw_text: str) -> str:
    """Surround detected heading lines with blank lines.

    normalize_text folds single line breaks into spaces (to rejoin wrapped
    paragraphs) but keeps blank-line-separated paragraphs intact. Isolating
    headings as their own paragraph here means they survive normalization
    as a standalone line, so downstream chunking can still detect them.
    """
    out: list[str] = []
    for line in raw_text.split("\n"):
        if detect_heading(line):
            out.extend(["", line, ""])
        else:
            out.append(line)
    return "\n".join(out)


def extract_pages(pdf_bytes: bytes) -> list[PageText]:
    """Extract normalized text per page, preserving 1-indexed page numbers."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except PdfReadError as exc:
        raise IngestionError(f"Could not parse PDF: {exc}") from exc

    pages: list[PageText] = []
    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        normalized = normalize_text(_isolate_headings(raw_text))
        if normalized:
            pages.append(PageText(number=page_number, text=normalized))
    return pages


def ingest_pdf(filename: str, content: bytes, paper_title: str | None = None) -> list[EvidenceChunk]:
    """Validate, store, extract, and chunk one uploaded PDF.

    Returns the list of EvidenceChunk objects for this paper. The PDF is
    persisted to local storage (storage_service) before parsing so a bad
    parse doesn't lose the original upload.
    """
    storage_service.validate_pdf_upload(filename, content)

    paper_id = storage_service.generate_paper_id()
    storage_service.save_pdf(paper_id, content)

    pages = extract_pages(content)
    if not pages:
        raise IngestionError(
            f"No extractable text found in {filename!r}. "
            "Scanned/image-only PDFs need OCR, which is out of scope for Phase 1."
        )

    title = paper_title or filename.rsplit(".", 1)[0]
    return chunk_pages(pages, paper_id=paper_id, paper_title=title)
