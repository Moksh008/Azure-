"""Local file storage for uploaded papers.

Phase 1: files live on local disk under STORAGE_ROOT. Phase 2 swaps this
module for an Azure Blob Storage-backed implementation; callers should only
depend on `save_pdf` / `read_pdf` / `paper_pdf_path`, not on the disk layout.
"""

from __future__ import annotations

import uuid
from pathlib import Path

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB per paper

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "papers"


class InvalidUploadError(ValueError):
    """Raised when an uploaded file fails validation."""


def generate_paper_id() -> str:
    return uuid.uuid4().hex[:12]


def validate_pdf_upload(filename: str | None, content: bytes) -> None:
    if not filename or not filename.lower().endswith(".pdf"):
        raise InvalidUploadError("Only .pdf files are accepted.")
    if not content:
        raise InvalidUploadError("Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise InvalidUploadError(
            f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB upload limit."
        )
    if not content.startswith(b"%PDF-"):
        raise InvalidUploadError("File does not look like a valid PDF.")


def paper_pdf_path(paper_id: str) -> Path:
    return STORAGE_ROOT / f"{paper_id}.pdf"


def save_pdf(paper_id: str, content: bytes) -> Path:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    path = paper_pdf_path(paper_id)
    path.write_bytes(content)
    return path


def read_pdf(paper_id: str) -> bytes:
    path = paper_pdf_path(paper_id)
    if not path.exists():
        raise FileNotFoundError(f"No stored PDF for paper_id={paper_id!r}")
    return path.read_bytes()
