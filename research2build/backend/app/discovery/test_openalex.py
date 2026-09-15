import asyncio

from openalex_client import format_paper_metadata, search_papers


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
