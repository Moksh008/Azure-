from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
