"""PDF -> text -> EvidenceChunk pipeline.

Upload validation and local storage: services/storage_service.py
Text normalization and heading detection: services/text_service.py
Chunk assembly: services/chunking_service.py

This module wires those pieces together into `ingest_pdf` (one PDF) and
`ingest_pdfs` (many PDFs, extracted in parallel) entry points used by the
API layer.
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from typing import Sequence

from shared.schemas import EvidenceChunk

from .services import storage_service
from .services.chunking_service import PageText, chunk_pages
from .services.text_service import detect_heading, normalize_text

try:  # PyMuPDF >= 1.24 prefers the `pymupdf` name; `fitz` is the legacy alias
    import pymupdf as fitz
except ImportError:  # pragma: no cover - only hit on very old PyMuPDF installs
    import fitz


class IngestionError(ValueError):
    """Raised when a PDF can't be validated or parsed into evidence."""


# ---------------------------------------------------------------------------
# Content-addressed caching: same PDF bytes -> same paper_id -> extraction,
# chunking, and (crucially) the caller's embedding call all get skipped on a
# re-upload. Without this, re-uploading an already-indexed paper burns a
# real Azure embedding API call for every chunk, every time (CLAUDE.md:
# "process each paper once ... never re-run extraction or embedding on
# every query").
# ---------------------------------------------------------------------------

def paper_id_for_content(content: bytes) -> str:
    """Deterministic paper_id derived from PDF bytes, replacing the old
    random uuid so identical uploads always resolve to the same id."""
    return storage_service.content_hash(content)


def _load_cached_chunks(paper_id: str) -> list[EvidenceChunk] | None:
    path = storage_service.paper_manifest_path(paper_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [EvidenceChunk(**item) for item in data]
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return None


def _save_chunks_manifest(paper_id: str, chunks: list[EvidenceChunk]) -> None:
    path = storage_service.paper_manifest_path(paper_id)
    path.write_text(
        json.dumps([chunk.model_dump() for chunk in chunks]),
        encoding="utf-8",
    )


def get_cached_chunks(content: bytes) -> list[EvidenceChunk] | None:
    """Previously computed chunks for this exact PDF content, if any.

    Callers should skip extraction, chunking, AND re-adding to the vector
    store when this returns non-None — the paper is already fully indexed.
    """
    return _load_cached_chunks(paper_id_for_content(content))


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
    """Extract normalized text per page, preserving 1-indexed page numbers.

    Uses PyMuPDF, which is considerably faster than pypdf on large documents.
    PyMuPDF is NOT thread-safe, so callers parallelizing across PDFs must use
    processes (see ingest_pdfs), never threads.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except (RuntimeError, ValueError) as exc:
        raise IngestionError(f"Could not parse PDF: {exc}") from exc

    pages: list[PageText] = []
    try:
        for page_number, page in enumerate(doc, start=1):
            raw_text = page.get_text() or ""
            normalized = normalize_text(_isolate_headings(raw_text))
            if normalized:
                pages.append(PageText(number=page_number, text=normalized))
    except (RuntimeError, ValueError) as exc:
        raise IngestionError(f"Could not extract PDF text: {exc}") from exc
    finally:
        doc.close()
    return pages


def _extract_job(job: tuple[int, str, bytes]) -> tuple[int, list[PageText]]:
    """Process-pool worker: extract one PDF's pages, carrying its input index.

    Module-level so it can be pickled (required for spawn-based pools on
    Windows). Extraction is pure CPU work with no filesystem access, so it is
    safe to run in child processes even when the parent patched module state.
    """
    index, filename, content = job
    try:
        return index, extract_pages(content)
    except IngestionError as exc:
        raise IngestionError(f"{filename}: {exc}") from exc


def _extract_pages_parallel(
    files: Sequence[tuple[str, bytes]],
    max_workers: int | None,
) -> list[list[PageText]]:
    """Extract pages for every PDF in parallel worker processes.

    Processes, not threads: PyMuPDF explicitly does not support multi-threaded
    use. Falls back to a sequential loop in environments where a process pool
    can't be created (restricted sandboxes, missing /dev/shm, ...).
    """
    jobs = [(idx, filename, content) for idx, (filename, content) in enumerate(files)]
    extracted: list[list[PageText] | None] = [None] * len(jobs)
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for index, pages in executor.map(_extract_job, jobs):
                extracted[index] = pages
    except IngestionError:
        raise  # a genuinely bad PDF — report it rather than silently retrying
    except (OSError, PermissionError, NotImplementedError, BrokenProcessPool):
        extracted = [extract_pages(content) for _, content in files]
    return [pages for pages in extracted if pages is not None]


def _persist_and_chunk(
    filename: str,
    content: bytes,
    pages: list[PageText],
    paper_title: str | None,
    paper_id_override: str | None,
) -> list[EvidenceChunk]:
    """Persist an already-extracted PDF and assemble its EvidenceChunks."""
    storage_id = paper_id_for_content(content)
    storage_service.save_pdf(storage_id, content)

    paper_id = paper_id_override or storage_id
    title = paper_title or filename.rsplit(".", 1)[0]
    chunks = chunk_pages(pages, paper_id=paper_id, paper_title=title)
    if not paper_id_override:
        _save_chunks_manifest(storage_id, chunks)
    return chunks


def ingest_pdf(
    filename: str,
    content: bytes,
    paper_title: str | None = None,
    paper_id_override: str | None = None,
    max_bytes: int = storage_service.MAX_UPLOAD_BYTES,
) -> list[EvidenceChunk]:
    """Validate, store, extract, and chunk one uploaded PDF.

    Returns the list of EvidenceChunk objects for this paper. The PDF is
    persisted to local storage (storage_service) before parsing so a bad
    parse doesn't lose the original upload.

    `paper_id_override` lets a caller pin the chunks' logical paper_id to
    one it already knows (e.g. an OpenAlex work id for a discovered paper
    whose full text is being fetched after the fact). Storage always uses
    its own filesystem-safe id internally (derived from content, never the
    override), since an OpenAlex id contains characters ("/", ":") that
    aren't valid in a file path on any platform.

    Without an override, the paper_id is derived deterministically from
    the PDF's content (see `paper_id_for_content`), so re-uploading the
    same file resolves to the same id. Callers that want to skip
    extraction entirely on a re-upload should check `get_cached_chunks`
    first — this function still does the full extract+chunk work.
    """
    storage_service.validate_pdf_upload(filename, content, max_bytes=max_bytes)

    storage_id = paper_id_for_content(content)
    storage_service.save_pdf(storage_id, content)

    pages = extract_pages(content)
    if not pages:
        raise IngestionError(
            f"No extractable text found in {filename!r}. "
            "Scanned/image-only PDFs need OCR, which is out of scope for Phase 1."
        )

    paper_id = paper_id_override or storage_id
    title = paper_title or filename.rsplit(".", 1)[0]
    chunks = chunk_pages(pages, paper_id=paper_id, paper_title=title)
    if not paper_id_override:
        _save_chunks_manifest(storage_id, chunks)
    return chunks


def ingest_pdfs(
    files: Sequence[tuple[str, bytes]],
    max_bytes: int = storage_service.MAX_UPLOAD_BYTES,
    max_workers: int | None = None,
) -> list[list[EvidenceChunk]]:
    """Validate, extract, store, and chunk several uploaded PDFs at once.

    Every file is validated up front, so one bad upload rejects the whole
    batch before any work happens (partial ingests are avoided). Text
    extraction — the CPU-heavy stage — then runs in parallel worker
    processes, while the persist + chunk steps run in the caller's process.
    Files that fail extraction are not persisted.

    Returns one EvidenceChunk list per input file, in input order.
    Pass max_workers=1 to keep extraction sequential (e.g. in tests that
    patch module state and want everything in-process).
    """
    for filename, content in files:
        try:
            storage_service.validate_pdf_upload(filename, content, max_bytes=max_bytes)
        except storage_service.InvalidUploadError as exc:
            raise storage_service.InvalidUploadError(f"{filename}: {exc}") from exc

    if len(files) > 1 and max_workers != 1:
        pages_per_file = _extract_pages_parallel(files, max_workers)
    else:
        pages_per_file = [extract_pages(content) for _, content in files]

    results: list[list[EvidenceChunk]] = []
    for (filename, content), pages in zip(files, pages_per_file):
        if not pages:
            raise IngestionError(
                f"No extractable text found in {filename!r}. "
                "Scanned/image-only PDFs need OCR, which is out of scope for Phase 1."
            )
        results.append(
            _persist_and_chunk(filename, content, pages, paper_title=None, paper_id_override=None)
        )
    return results
