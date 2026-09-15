from dataclasses import dataclass


@dataclass
class EvidenceChunk:
    chunk_id: str
    paper_id: str
    title: str
    text: str
    source_url: str | None = None
    page_number: int | None = None
    section: str | None = None
