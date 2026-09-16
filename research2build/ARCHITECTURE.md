# Architecture foundation

## Initial flow

User -> Frontend -> FastAPI -> focused services -> evidence index -> grounded generation.

## Stable contracts

The most important shared contract is `EvidenceChunk`. Retrieval implementations may change from a local vector store to Azure AI Search, but downstream features should continue receiving the same fields:

- `chunk_id`
- `paper_id`
- `paper_title`
- `section`
- `page`
- `text`

## Ownership

1. Discovery and ingestion
2. Discovery and retrieval
3. Paper analysis and Q&A
4. Opportunity, project, feasibility, PRD
5. Frontend and integration

Use pull requests and avoid editing another member's owned module without agreement.
