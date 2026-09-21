"""Pick the evidence chunks worth sending to the LLM.

A full-text paper can be tens of thousands of tokens, far more than fits in
a model's context window (a local Ollama model defaults to 4096 tokens and
silently drops the rest). Rather than send every chunk of every selected
paper, rank chunks against the question with BM25 and keep the best ones
within a character budget. Chunks are returned whole and unmodified, so
citations still quote real source text.

Papers share the budget fairly: every paper gets its best chunk before any
paper gets a second one. Questions with no keyword overlap (e.g. "what is
this paper about?") fall back to a paper's opening chunks, which is where
the abstract lives.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter

from shared.schemas import EvidenceChunk

# ~4 chars per token: 8000 chars is ~2000 tokens, leaving room for the
# prompt template and the answer inside a 4096-token context.
DEFAULT_CHAR_BUDGET = 8000
FALLBACK_LEADING_CHUNKS = 2

BM25_K1 = 1.5
BM25_B = 0.75

_STOPWORDS = frozenset(
    """a an and are as at be been but by can could did do does for from had has
    have how i if in into is it its of on or our paper papers study that the
    their them these this those to was we were what when where which who why
    will with would you your about according also any some than then there
    they not no all each both such via using use used""".split()
)


def char_budget() -> int:
    """Per-request evidence budget; override with CHAT_EVIDENCE_CHAR_BUDGET
    when the model has a bigger context window."""
    try:
        return int(os.getenv("CHAT_EVIDENCE_CHAR_BUDGET", DEFAULT_CHAR_BUDGET))
    except ValueError:
        return DEFAULT_CHAR_BUDGET


def _tokenize(text: str) -> list[str]:
    tokens = []
    for word in re.findall(r"\w+", text.lower()):
        if len(word) < 2 or word in _STOPWORDS:
            continue
        if len(word) > 3 and word.endswith("s"):
            word = word[:-1]
        tokens.append(word)
    return tokens


def _bm25_scores(chunks: list[EvidenceChunk], query: str) -> list[float]:
    query_terms = set(_tokenize(query))
    docs = [Counter(_tokenize(c.text)) for c in chunks]
    lengths = [sum(d.values()) for d in docs]
    average_length = (sum(lengths) / len(lengths)) if lengths else 0.0

    scores = [0.0] * len(chunks)
    if not query_terms or average_length == 0:
        return scores

    for term in query_terms:
        containing = sum(1 for d in docs if term in d)
        if containing == 0:
            continue
        idf = math.log(1 + (len(chunks) - containing + 0.5) / (containing + 0.5))
        for i, doc in enumerate(docs):
            frequency = doc.get(term, 0)
            if frequency == 0:
                continue
            norm = 1 - BM25_B + BM25_B * lengths[i] / average_length
            scores[i] += idf * frequency * (BM25_K1 + 1) / (frequency + BM25_K1 * norm)
    return scores


def select_evidence(
    chunks: list[EvidenceChunk],
    query: str,
    budget: int | None = None,
    lead_chunks: int = 0,
) -> list[EvidenceChunk]:
    """Return the chunks most relevant to `query`, within `budget` characters.

    `lead_chunks` force-includes each paper's first N chunks (title/abstract)
    before ranking — useful for whole-paper analysis. Output keeps the input
    order so the selected passages still read in document order.
    """
    budget = char_budget() if budget is None else budget
    if sum(len(c.text) for c in chunks) <= budget:
        return list(chunks)

    scores = _bm25_scores(chunks, query)

    by_paper: dict[str, list[int]] = {}
    for index, chunk in enumerate(chunks):
        by_paper.setdefault(chunk.paper_id, []).append(index)

    chosen: set[int] = set()
    used = 0

    def take(index: int) -> None:
        nonlocal used
        cost = len(chunks[index].text)
        if index in chosen or (chosen and used + cost > budget):
            return
        chosen.add(index)
        used += cost

    for indices in by_paper.values():
        for index in indices[:lead_chunks]:
            take(index)

    ranked: dict[str, list[int]] = {}
    for paper_id, indices in by_paper.items():
        positive = sorted(
            (i for i in indices if scores[i] > 0), key=lambda i: (-scores[i], i)
        )
        ranked[paper_id] = positive or indices[:FALLBACK_LEADING_CHUNKS]

    depth = max((len(r) for r in ranked.values()), default=0)
    for rank in range(depth):
        for paper_id in by_paper:
            if rank < len(ranked[paper_id]):
                take(ranked[paper_id][rank])

    return [chunks[i] for i in sorted(chosen)]
