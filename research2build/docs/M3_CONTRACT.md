# M3 Contract — AI Paper Analysis + Evidence-Based Q&A

## Purpose

M3 provides evidence-grounded paper analysis and question answering.

M3 never treats unsupported LLM-generated evidence IDs as valid citations.

## Inputs

### EvidenceChunk

```text
chunk_id
paper_id
paper_title
section
page
text
```

### Q&A

```text
question
evidence[]
```

### Retrieval-based Q&A

```text
question
top_k
```

### Paper Analysis

```text
paper_id
paper_title
evidence[]
```

## Outputs

### GroundedAnswer

```text
answer
citations[]
evidence_sufficient
```

### Citation

```text
chunk_id
paper_id
paper_title
section
page
quote
```

### GroundedClaim

```text
claim
citations[]
```

### PaperAnalysis

```text
paper_id
paper_title
problem
objective
methodology
dataset
models
results[]
limitations[]
future_work[]
```

## API Endpoints

### POST /qa

Performs grounded Q&A using supplied evidence.

### POST /qa/retrieve

Retrieves evidence through M2 and performs grounded Q&A.

### POST /analysis

Performs structured grounded paper analysis using supplied evidence.

## Grounding Guarantee

Every grounded claim must contain at least one citation.

Every citation must correspond to an evidence chunk supplied to M3.

If the LLM references an unknown evidence ID, M3 raises a validation error.

If retrieval returns no evidence for Q&A, M3 returns `evidence_sufficient = false`
and does not call the LLM.

## M2 → M3 Contract

M3 depends only on the shared `EvidenceChunk` schema. M3 does not depend on
M2's internal retrieval implementation. Therefore the retrieval implementation
can later be replaced with Azure AI Search without changing the M3 output
contract.

## M3 → M4 Contract

M4 can consume:

- `PaperAnalysis.problem`
- `PaperAnalysis.objective`
- `PaperAnalysis.methodology`
- `PaperAnalysis.results`
- `PaperAnalysis.limitations`
- `PaperAnalysis.future_work`

Each `GroundedClaim` contains citations that preserve the original paper
evidence. M4 can identify recurring research gaps while retaining evidence
traceability.

## M3 → Frontend/M5 Contract

The frontend can display the answer, paper title, section, page, evidence quote,
and evidence sufficiency without accessing M3 internals.

## Version

Contract version: 1.0
