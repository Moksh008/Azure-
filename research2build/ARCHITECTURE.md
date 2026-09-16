# Architecture foundation

## Initial flow

User -> Frontend -> FastAPI -> focused services -> evidence index -> grounded generation.

## Stable contracts

**Contract freeze (v1.0), effective now.** `EvidenceChunk` and `Citation` in
`shared/schemas.py` are the frozen interface between ingestion (M1),
retrieval/embeddings (M2), and analysis/Q&A/RAG (M3). No existing field
may be renamed, retyped, or removed without agreement from all three
owners; new optional fields may be proposed via PR. See the docstrings in
`shared/schemas.py` for full field semantics.

`EvidenceChunk` — produced by ingestion, indexed and returned by
retrieval. Downstream features must keep receiving the same fields even
as the retrieval implementation changes from a local vector store to
Azure AI Search:

- `chunk_id` — unique within a paper (`{paper_id}-{0001...}`)
- `paper_id` — unique per ingested paper
- `paper_title`
- `section` — canonical section name, or `None` if undetected
- `page` — 1-indexed page number
- `text` — normalized chunk text; the unit M2 embeds and M3 quotes from

`Citation` — the grounding every LLM-generated claim must carry (built
from an `EvidenceChunk` via `Citation.from_chunk`). Same identifying
fields as `EvidenceChunk`, plus:

- `quote` — the short excerpt of the chunk's text that actually supports
  the claim, not the full chunk

Any function that returns a generated claim (Q&A answer, analysis field,
opportunity, project) must return `Citation`s alongside it — no ungrounded
claims.

## Ownership

1. Discovery and ingestion
2. Discovery and retrieval
3. Paper analysis and Q&A
4. Opportunity, project, feasibility, PRD
5. Frontend and integration

Use pull requests and avoid editing another member's owned module without agreement.
