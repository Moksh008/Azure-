"""File storage for uploaded papers.

Supports Azure Blob Storage (when AZURE_STORAGE_CONNECTION_STRING is configured)
with graceful fallback to local disk storage under STORAGE_ROOT.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

logger = logging.getLogger("research2build.storage")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB per manually uploaded paper
# Publisher-typeset open-access PDFs embed high-res figures and are often
# well over 25 MB (e.g. a 44 MB Nature paper), so fetched copies get a
# higher cap than manual uploads.
MAX_FETCHED_PDF_BYTES = 60 * 1024 * 1024

STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "papers"
AZURE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER", "papers")


class InvalidUploadError(ValueError):
    """Raised when an uploaded file fails validation."""


def generate_paper_id() -> str:
    return uuid.uuid4().hex[:12]


def validate_pdf_upload(
    filename: str | None,
    content: bytes,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> None:
    if not filename or not filename.lower().endswith(".pdf"):
        raise InvalidUploadError("Only .pdf files are accepted.")
    if not content:
        raise InvalidUploadError("Uploaded file is empty.")
    if len(content) > max_bytes:
        raise InvalidUploadError(
            f"File exceeds the {max_bytes // (1024 * 1024)}MB upload limit."
        )
    if not content.startswith(b"%PDF-"):
        raise InvalidUploadError("File does not look like a valid PDF.")


def paper_pdf_path(paper_id: str) -> Path:
    return STORAGE_ROOT / f"{paper_id}.pdf"


def _get_blob_client(blob_name: str):
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        return None
    try:
        from azure.storage.blob import BlobServiceClient

        service_client = BlobServiceClient.from_connection_string(conn_str)
        container_client = service_client.get_container_client(AZURE_CONTAINER_NAME)
        if not container_client.exists():
            container_client.create_container()
        return container_client.get_blob_client(blob_name)
    except Exception as exc:
        logger.warning(f"Failed to connect to Azure Blob Storage: {exc}")
        return None


def save_pdf(paper_id: str, content: bytes) -> Path:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    path = paper_pdf_path(paper_id)
    path.write_bytes(content)

    blob_client = _get_blob_client(f"{paper_id}.pdf")
    if blob_client:
        try:
            blob_client.upload_blob(content, overwrite=True)
            logger.info(f"Uploaded paper {paper_id}.pdf to Azure Blob container '{AZURE_CONTAINER_NAME}'.")
        except Exception as exc:
            logger.warning(f"Failed to upload {paper_id}.pdf to Azure Blob Storage: {exc}")

    return path


def read_pdf(paper_id: str) -> bytes:
    path = paper_pdf_path(paper_id)
    if path.exists():
        return path.read_bytes()

    blob_client = _get_blob_client(f"{paper_id}.pdf")
    if blob_client and blob_client.exists():
        try:
            data = blob_client.download_blob().readall()
            STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return data
        except Exception as exc:
            logger.warning(f"Failed to download {paper_id}.pdf from Azure Blob Storage: {exc}")

    raise FileNotFoundError(f"No stored PDF for paper_id={paper_id!r}")

