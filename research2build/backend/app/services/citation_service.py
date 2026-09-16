"""Builds the grounding objects (Citation, GroundedClaim) that every
LLM-generated claim must carry.

Ingestion (M1) owns this module alongside the frozen EvidenceChunk/Citation
contract (see shared/schemas.py, ARCHITECTURE.md). Downstream consumers
(M3 analysis/Q&A, M4 opportunity/project generation) should build their
Citations and GroundedClaims through these functions rather than
constructing the models by hand, so the "no ungrounded claim" rule is
enforced in one place instead of at every call site.
"""

from __future__ import annotations

from shared.schemas import Citation, EvidenceChunk, GroundedClaim


class UngroundedClaimError(ValueError):
    """Raised when a claim has no supporting chunk to cite."""


def cite_chunk(chunk: EvidenceChunk, quote: str | None = None) -> Citation:
    """Build a Citation from one EvidenceChunk.

    `quote` should be the smallest excerpt of `chunk.text` that actually
    supports the claim; defaults to the full chunk text when the caller
    can't isolate a shorter span.
    """
    return Citation.from_chunk(chunk, quote=quote)


def cite_chunks(
    chunks: list[EvidenceChunk], quotes: list[str | None] | None = None
) -> list[Citation]:
    """Build one Citation per chunk, in order.

    `quotes`, if given, must be the same length as `chunks`; each entry
    pairs positionally with the chunk at the same index (None falls back
    to the full chunk text for that entry).
    """
    if quotes is None:
        quotes = [None] * len(chunks)
    if len(quotes) != len(chunks):
        raise ValueError("quotes must be the same length as chunks when provided")
    return [cite_chunk(chunk, quote) for chunk, quote in zip(chunks, quotes)]


def make_grounded_claim(
    claim: str,
    chunks: list[EvidenceChunk],
    quotes: list[str | None] | None = None,
) -> GroundedClaim:
    """Attach citations to a generated claim.

    Raises UngroundedClaimError if `chunks` is empty — callers must not
    produce a claim without at least one supporting chunk.
    """
    if not chunks:
        raise UngroundedClaimError(f"Claim has no supporting evidence: {claim!r}")
    return GroundedClaim(claim=claim, citations=cite_chunks(chunks, quotes))
