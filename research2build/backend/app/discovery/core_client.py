"""CORE (core.ac.uk) search — a large aggregator of open-access research
papers. Complements OpenAlex: CORE often has a direct open-access PDF link
where OpenAlex has none.

Needs CORE_API_KEY (free at https://core.ac.uk/services/api). Without it
the client simply isn't used (see `CoreClient.from_env`).
"""

from __future__ import annotations

import os

import requests

from backend.app.discovery.paper_models import Paper


class CoreClient:
    # The trailing slash matters: without it CORE answers 301 and some
    # HTTP clients drop the Authorization header when following it.
    SEARCH_URL = "https://api.core.ac.uk/v3/search/works/"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @classmethod
    def from_env(cls) -> "CoreClient | None":
        api_key = os.getenv("CORE_API_KEY", "").strip()
        return cls(api_key) if api_key else None

    def search_papers(self, query: str, max_results: int = 20) -> list[Paper]:
        response = requests.get(
            self.SEARCH_URL,
            params={"q": query, "limit": max_results},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=20,
        )
        response.raise_for_status()

        papers = []
        for result in response.json().get("results", []):
            title = (result.get("title") or "").strip()
            if not title:
                continue

            papers.append(
                Paper(
                    paper_id=f"core:{result.get('id')}",
                    title=title,
                    abstract=(result.get("abstract") or "").strip(),
                    authors=[
                        a["name"] for a in result.get("authors") or [] if a.get("name")
                    ],
                    publication_year=result.get("yearPublished"),
                    doi=result.get("doi"),
                    url=self._landing_url(result),
                    pdf_url=result.get("downloadUrl") or None,
                )
            )

        return papers

    @staticmethod
    def _landing_url(result: dict) -> str | None:
        for link in result.get("links") or []:
            if link.get("type") == "display" and link.get("url"):
                return link["url"]
        return f"https://core.ac.uk/works/{result['id']}" if result.get("id") else None
