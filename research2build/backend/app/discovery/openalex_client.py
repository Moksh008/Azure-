from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class PaperMetadata:
    paper_id: str | None
    title: str | None
    authors: list[str]
    publication_year: int | None
    doi: str | None
    source_name: str | None
    source_url: str | None
    open_access: bool | None
    abstract: str


OPENALEX_API_URL = "https://api.openalex.org/works"


async def search_papers(
    topic: str,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """
    Search OpenAlex for research papers related to a topic.

    Returns basic metadata for each paper.
    """

    params = {
        "search": topic,
        "per-page": per_page,
        "select": (
            "id,title,publication_year,doi,authorships,"
            "primary_location,open_access,abstract_inverted_index"
        ),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(OPENALEX_API_URL, params=params)
        response.raise_for_status()

        data = response.json()

    return data.get("results", [])


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""

    words: list[str] = []

    for word, positions in inverted_index.items():
        for position in positions:
            while len(words) <= position:
                words.append("")
            words[position] = word

    return " ".join(words)


def format_paper_metadata(paper: dict[str, Any]) -> PaperMetadata:
    authors = []

    for authorship in paper.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name")

        if name:
            authors.append(name)

    primary_location = paper.get("primary_location") or {}
    source = primary_location.get("source") or {}

    return PaperMetadata(
        paper_id=paper.get("id"),
        title=paper.get("title"),
        authors=authors,
        publication_year=paper.get("publication_year"),
        doi=paper.get("doi"),
        source_name=source.get("display_name"),
        source_url=primary_location.get("landing_page_url"),
        open_access=(paper.get("open_access") or {}).get("is_oa"),
        abstract=reconstruct_abstract(
            paper.get("abstract_inverted_index")
        ),
    )