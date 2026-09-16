import requests

try:
    from app.discovery.paper_models import Paper
except ImportError:
    from paper_models import Paper


class OpenAlexClient:
    BASE_URL = "https://api.openalex.org/works"

    def search_papers(
        self,
        query: str,
        max_results: int = 20,
    ) -> list[Paper]:
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
            )

            papers.append(paper)

        return papers

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