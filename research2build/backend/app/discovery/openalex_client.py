import hashlib
import threading
import time

import requests

try:
    from backend.app.discovery.paper_models import Paper
except ImportError:
    try:
        from app.discovery.paper_models import Paper
    except ImportError:
        from paper_models import Paper


# Module-level cache, keyed by a hash of the normalized query + result
# count, so identical searches (e.g. repeated by the same or different
# users within the TTL window) don't burn OpenAlex's rate limit again.
# Process-local and unbounded-but-short-lived by design — this is a single
# Container-Apps instance for a class project, not a multi-node deployment.
_CACHE_TTL_SECONDS = 3600
_cache_lock = threading.Lock()
_search_cache: dict[str, tuple[float, list[Paper]]] = {}


def _cache_key(query: str, max_results: int) -> str:
    normalized = " ".join(query.strip().lower().split())
    return hashlib.sha256(f"{normalized}|{max_results}".encode("utf-8")).hexdigest()


def clear_search_cache() -> None:
    """Test seam — drop all cached OpenAlex results."""
    with _cache_lock:
        _search_cache.clear()


class OpenAlexClient:
    BASE_URL = "https://api.openalex.org/works"

    def search_papers(
        self,
        query: str,
        max_results: int = 20,
    ) -> list[Paper]:
        cache_key = _cache_key(query, max_results)
        with _cache_lock:
            cached = _search_cache.get(cache_key)
        if cached is not None:
            cached_at, papers = cached
            if time.monotonic() - cached_at < _CACHE_TTL_SECONDS:
                return list(papers)

        params = {
            "search": query,
            "per-page": max_results,
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        papers = []

        for result in data.get("results", []):
            abstract = self._extract_abstract(result)

            paper = Paper(
                paper_id=result.get("id", ""),
                title=result.get("title", ""),
                abstract=abstract,
                authors=self._extract_authors(result),
                publication_year=result.get("publication_year"),
                doi=result.get("doi"),
                url=result.get("primary_location", {}).get("landing_page_url")
                if result.get("primary_location")
                else None,
                pdf_url=self._extract_pdf_url(result),
            )

            papers.append(paper)

        with _cache_lock:
            _search_cache[cache_key] = (time.monotonic(), list(papers))

        return papers

    def pdf_candidates(self, work_id: str, limit: int = 5) -> list[str]:
        """Every distinct PDF link OpenAlex knows for one work (publisher
        copy, arXiv, PMC, repositories, ...), for when the first fails.

        Best-effort: any lookup failure just yields no extra candidates.
        """
        short_id = work_id.rstrip("/").rsplit("/", 1)[-1]
        try:
            response = requests.get(f"{self.BASE_URL}/{short_id}", timeout=15)
            response.raise_for_status()
            work = response.json()
        except (requests.RequestException, ValueError):
            return []

        urls: list[str] = []
        locations = [work.get("best_oa_location"), work.get("primary_location")]
        locations += work.get("locations") or []
        for location in locations:
            pdf_url = (location or {}).get("pdf_url")
            if pdf_url and pdf_url not in urls:
                urls.append(pdf_url)

        oa_url = (work.get("open_access") or {}).get("oa_url")
        if oa_url and oa_url not in urls:
            urls.append(oa_url)

        return urls[:limit]

    @staticmethod
    def _extract_pdf_url(result: dict) -> str | None:
        """Best available direct PDF link, when this work is open access.

        Not every paper has one — paywalled works simply have no usable
        location here, and callers must fall back to abstract-only.
        """
        for location_key in ("best_oa_location", "primary_location"):
            location = result.get(location_key)
            if location and location.get("pdf_url"):
                return location["pdf_url"]

        open_access = result.get("open_access") or {}
        if open_access.get("is_oa") and open_access.get("oa_url"):
            return open_access["oa_url"]

        return None

    @staticmethod
    def _extract_authors(result: dict) -> list[str]:
        authors = []

        for author_entry in result.get("authorships", []):
            author = author_entry.get("author", {})
            display_name = author.get("display_name")

            if display_name:
                authors.append(display_name)

        return authors

    @staticmethod
    def _extract_abstract(result: dict) -> str:
        inverted_index = result.get("abstract_inverted_index")

        if not inverted_index:
            return ""

        words = []

        for word, positions in inverted_index.items():
            for position in positions:
                words.append((position, word))

        words.sort(key=lambda item: item[0])

        return " ".join(word for _, word in words)