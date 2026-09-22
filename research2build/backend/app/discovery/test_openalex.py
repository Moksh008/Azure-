from unittest.mock import MagicMock, patch

try:
    from app.discovery.openalex_client import OpenAlexClient, clear_search_cache
    from app.discovery.paper_models import Paper
except ImportError:
    from openalex_client import OpenAlexClient, clear_search_cache
    from paper_models import Paper


def test_paper_model_instantiation():
    paper = Paper(
        paper_id="W12345",
        title="Test Paper",
        abstract="Test Abstract",
        authors=["Author One"],
        publication_year=2024,
    )
    assert paper.paper_id == "W12345"
    assert paper.title == "Test Paper"
    assert paper.authors == ["Author One"]


def test_openalex_client_extract_abstract():
    inverted_index = {"hello": [0], "world": [1]}
    abstract = OpenAlexClient._extract_abstract(
        {"abstract_inverted_index": inverted_index}
    )
    assert abstract == "hello world"


def test_openalex_client_extract_authors():
    sample_result = {
        "authorships": [
            {"author": {"display_name": "Alice"}},
            {"author": {"display_name": "Bob"}},
        ]
    }
    authors = OpenAlexClient._extract_authors(sample_result)
    assert authors == ["Alice", "Bob"]


def _mock_response(titles: list[str]):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "results": [
            {"id": f"W{i}", "title": title, "authorships": []}
            for i, title in enumerate(titles)
        ]
    }
    return response


def test_search_papers_caches_by_query_hash():
    """Same query + max_results within the TTL -> only one HTTP call, so
    repeated searches don't burn OpenAlex's rate limit (CLAUDE.md-adjacent
    cost discipline for the discovery flow)."""
    clear_search_cache()
    client = OpenAlexClient()

    with patch("requests.get", return_value=_mock_response(["Paper A"])) as mock_get:
        first = client.search_papers("federated learning", max_results=5)
        second = client.search_papers("federated learning", max_results=5)

    assert mock_get.call_count == 1
    assert [p.title for p in first] == [p.title for p in second] == ["Paper A"]


def test_search_papers_cache_is_keyed_by_query_and_max_results():
    clear_search_cache()
    client = OpenAlexClient()

    with patch("requests.get", return_value=_mock_response(["Paper A"])) as mock_get:
        client.search_papers("federated learning", max_results=5)
        client.search_papers("federated learning", max_results=10)  # different key
        client.search_papers("  Federated   Learning  ", max_results=5)  # same key, normalized

    assert mock_get.call_count == 2


def main():
    client = OpenAlexClient()

    papers = client.search_papers(
        "machine learning healthcare",
        max_results=5,
    )

    for paper in papers:
        print("=" * 60)
        print("Title:", paper.title)
        print("Year:", paper.publication_year)
        print("Authors:", ", ".join(paper.authors))
        print("Abstract:", paper.abstract[:500])
        print("URL:", paper.url)


if __name__ == "__main__":
    main()
