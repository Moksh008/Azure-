"""Splits normalized, section-tagged page text into EvidenceChunk objects."""

from __future__ import annotations

from dataclasses import dataclass

from shared.schemas import EvidenceChunk

from .text_service import detect_heading

CHUNK_SIZE = 1000  # target characters per chunk
CHUNK_OVERLAP = 150  # characters carried into the next chunk within a section


@dataclass
class PageText:
    number: int
    text: str


def chunk_pages(
    pages: list[PageText],
    paper_id: str,
    paper_title: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[EvidenceChunk]:
    """Turn per-page text into EvidenceChunks, tracking section and page.

    Walks lines in reading order, detecting headings to tag the current
    section, and accumulates non-heading lines into ~chunk_size chunks. A
    chunk boundary at a section change starts fresh (no overlap, to avoid
    mixing two sections' evidence); a boundary hit purely by size carries
    a small overlap so retrieval doesn't lose context at the cut.
    """
    chunks: list[EvidenceChunk] = []
    current_section: str | None = None
    buffer = ""
    buffer_page: int | None = None
    chunk_index = 0

    def flush(carry_overlap: bool) -> None:
        nonlocal buffer, buffer_page, chunk_index
        text = buffer.strip()
        if text:
            chunk_index += 1
            chunks.append(
                EvidenceChunk(
                    chunk_id=f"{paper_id}-{chunk_index:04d}",
                    paper_id=paper_id,
                    paper_title=paper_title,
                    section=current_section,
                    page=buffer_page,
                    text=text,
                )
            )
        buffer = text[-overlap:] if carry_overlap and text else ""
        buffer_page = None

    for page in pages:
        for raw_line in page.text.splitlines():
            heading = detect_heading(raw_line)
            if heading:
                flush(carry_overlap=False)
                current_section = heading
                continue

            line = raw_line.strip()
            if not line:
                continue

            if buffer_page is None:
                buffer_page = page.number

            candidate = f"{buffer} {line}".strip() if buffer else line
            if len(candidate) > chunk_size and buffer:
                flush(carry_overlap=True)
                buffer_page = page.number
                candidate = f"{buffer} {line}".strip() if buffer else line

            buffer = candidate
            if len(buffer) >= chunk_size:
                flush(carry_overlap=True)
                buffer_page = page.number

    flush(carry_overlap=False)
    return chunks
