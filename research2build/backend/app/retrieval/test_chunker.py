from chunker import chunk_text


def main():
    text = """
    Fake news detection is an important research area.
    Social media platforms allow information to spread quickly.
    Researchers use linguistic, social, and network features.
    Machine learning models can classify suspicious content.
    However, datasets and evaluation methods differ across studies.
    """

    chunks = chunk_text(
        text,
        max_words=10,
        overlap_words=2,
    )

    print(f"Created {len(chunks)} chunks.\n")

    for index, chunk in enumerate(chunks, start=1):
        print(f"Chunk {index}:")
        print(chunk)
        print()


if __name__ == "__main__":
    main()
