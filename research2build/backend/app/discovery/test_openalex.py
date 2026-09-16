import asyncio

from app.discovery.openalex_client import (
    format_paper_metadata,
    reconstruct_abstract,
    search_papers,
)


def test_reconstruct_abstract():
    inverted_index = {"hello": [0], "world": [1]}
    assert reconstruct_abstract(inverted_index) == "hello world"
    assert reconstruct_abstract(None) == ""


def test_format_paper_metadata():
    sample_paper = {
        "id": "W123456789",
        "title": "Test Paper",
        "authorships": [{"author": {"display_name": "John Doe"}}],
        "publication_year": 2024,
        "doi": "https://doi.org/10.1234/test",
        "primary_location": {
            "source": {"display_name": "Journal of Testing"},
            "landing_page_url": "https://example.com",
        },
        "open_access": {"is_oa": True},
        "abstract_inverted_index": {"test": [0], "abstract": [1]},
    }
    metadata = format_paper_metadata(sample_paper)
    assert metadata.paper_id == "W123456789"
    assert metadata.title == "Test Paper"
    assert metadata.authors == ["John Doe"]
    assert metadata.publication_year == 2024
    assert metadata.doi == "https://doi.org/10.1234/test"
    assert metadata.source_name == "Journal of Testing"
    assert metadata.source_url == "https://example.com"
    assert metadata.open_access is True
    assert metadata.abstract == "test abstract"


async def main():
    topic = input("Enter a research topic: ")

    papers = await search_papers(topic, per_page=5)

    print(f"\nFound {len(papers)} papers.\n")

    for index, paper in enumerate(papers, start=1):
        metadata = format_paper_metadata(paper)

        print(f"{index}. {metadata.title}")
        print(f"   Year: {metadata.publication_year}")
        print(f"   Authors: {', '.join(metadata.authors[:3])}")

        if metadata.doi:
            print(f"   DOI: {metadata.doi}")

        if metadata.abstract:
            print(f"   Abstract: {metadata.abstract[:300]}...")

        if metadata.source_name:
            print(f"   Source: {metadata.source_name}")

        print(f"   Open Access: {metadata.open_access}")
        print(f"   URL: {metadata.source_url}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
