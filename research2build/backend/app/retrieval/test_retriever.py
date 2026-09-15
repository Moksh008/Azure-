import asyncio

from app.retrieval.demo_retriever import DemoRetriever


async def main():
    retriever = DemoRetriever()

    question = input("Enter a question: ")
    chunks = await retriever.retrieve(question, top_k=2)

    print(f"\nRetrieved {len(chunks)} evidence chunks.\n")

    for index, chunk in enumerate(chunks, start=1):
        print(f"{index}. {chunk.title}")
        print(f"   Text: {chunk.text}")
        print(f"   Section: {chunk.section}")
        print(f"   Page: {chunk.page_number}")
        print(f"   Source: {chunk.source_url}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
