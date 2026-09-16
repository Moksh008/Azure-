def chunk_text(
    text: str,
    max_words: int = 100,
    overlap_words: int = 20,
) -> list[str]:
    if not text.strip():
        return []

    words = text.split()
    chunks = []

    start = 0

    while start < len(words):
        end = start + max_words
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap_words

    return chunks
