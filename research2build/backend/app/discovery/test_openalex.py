try:
    from app.discovery.openalex_client import OpenAlexClient
    from app.discovery.paper_models import Paper
except ImportError:
    from openalex_client import OpenAlexClient
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
