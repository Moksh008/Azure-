import asyncio

from app.retrieval.openalex_retriever import OpenAlexRetriever


def test_openalex_retriever_instantiation():
    retriever = OpenAlexRetriever()
    assert retriever is not None


async def main():
    retriever = OpenAlexRetriever()

    question = input("Enter a research question: ")
    chunks = await retriever.retrieve(question, top_k=5)

    print(f"\nRetrieved {len(chunks)} evidence chunks.\n")

    for index, chunk in enumerate(chunks, start=1):
        print(f"{index}. {chunk.title}")
        print(f"   Text: {chunk.text[:300]}...")
        print(f"   Section: {chunk.section}")
        print(f"   Source: {chunk.source_url}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
