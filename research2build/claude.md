# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Research2Build — an AI system that turns a set of uploaded research papers into evidence-grounded Q&A, potential research opportunities, and feasibility-checked project proposals. Built for an AI-103 university project on a limited Azure for Students budget ($100 credit).

Core pipeline: papers → chunks → embeddings → retrieval → grounded LLM answers → opportunity → project proposal.

The single most important design constraint: every generated claim must be traceable to a specific paper/section/page. Do not let any code path produce an ungrounded claim without a citation. This is the project's main differentiator and its main grading criterion — treat it as non-negotiable, not a nice-to-have.

**Repository status:** pre-implementation. No backend/frontend code exists yet — only this planning doc. There are no build, lint, or test commands to run until Phase 1 scaffolding below is created.

## Current build phase

Check this before making changes — don't add cloud service code ahead of the phase we're in.

- **Phase 1 — Local skeleton.** FastAPI backend, local PDF extraction, local chunking, local vector store (Chroma/FAISS), direct LLM API calls. No Azure SDKs yet.
- **Phase 2 — Azure swap-in.** Replace local vector store with Azure AI Search, local LLM calls with Azure AI Foundry, local file storage with Blob Storage — one service at a time, keeping interfaces identical.
- **Phase 3 — Deploy.** Azure Static Web Apps (frontend) + Azure Container Apps (backend, scale-to-zero).

Update this section as phases complete. Assume Phase 1 unless told otherwise.

## Scope discipline

The MVP is exactly 5 capabilities. Do not add agents, features, or Azure services beyond this without being asked:

1. Paper upload → text extraction → chunking
2. Structured per-paper analysis (problem, method, results, limitations, future work)
3. Evidence-based Q&A with citations (paper, section, page)
4. Opportunity → Project generation from recurring evidence
5. Feasibility scoring + basic roadmap from user-provided constraints (team size, time, budget, skills)

Anything from the original brainstorm not in this list (multi-agent orchestration beyond a single orchestrator, architecture-diagram generation, GitHub export, evaluation dashboard) is Phase 2 / stretch — mention it only in docs, don't scaffold code for it.

## Planned repository structure

```
research2build/
├── backend/
│   ├── main.py              # FastAPI app + routes
│   ├── ingestion.py         # PDF -> text -> chunks
│   ├── embeddings.py        # embed + store (local or Azure AI Search)
│   ├── retrieval.py         # query -> top-k chunks; keep this interface
│   │                        # stable across the local -> Azure swap
│   ├── agents/
│   │   ├── analyzer.py      # per-paper structured extraction
│   │   ├── qa.py            # grounded Q&A with citations
│   │   └── project_gen.py   # opportunity -> project -> feasibility
│   └── requirements.txt
└── frontend/                # React, added after backend MVP works
```

Keep `retrieval.py`'s function signatures stable when swapping the underlying store (local FAISS/Chroma → Azure AI Search) so the rest of the app doesn't change.

## Conventions

- **Python:** FastAPI backend, type hints on all function signatures, pydantic models for structured LLM outputs (paper analysis, project proposals) rather than parsing free-text.
- **LLM calls:** always request structured JSON output for anything downstream code will parse (paper profiles, opportunities, projects). Never regex-parse free text when a JSON schema will do.
- **Citations:** every chunk carries `{paper_id, section, page}` metadata from ingestion onward. Any function that returns an LLM-generated claim must also return the supporting chunk metadata. If a code path can't attach evidence, flag it — don't silently drop grounding.
- **Cost awareness:** process each paper once (extract, chunk, embed) and persist the result — never re-run extraction or embedding on every query. Minimize LLM calls per user action; batch where possible.
- **Secrets:** local `.env` for API keys during Phase 1; move to Azure Key Vault / environment variables only in Phase 3. Never commit keys.

## Responsible AI language

The system must never claim to have discovered a research gap. Required phrasing in both UI copy and generated text:

- "Potential research opportunity" (not "research gap" or "discovery")
- "Inferred from recurring limitations in the provided papers" (not stated as fact)
- Include a "Novelty confidence: requires human validation" note on every generated opportunity/project

Enforce this in the prompt templates for `project_gen.py`, not just in the frontend copy — the underlying generated text should carry the hedge, not just the UI wrapper.

## What not to do

- Don't add Azure SDK calls while still in Phase 1.
- Don't build the full 7-agent pipeline from the original brainstorm doc — one orchestrator calling focused functions is enough and much easier to debug/grade.
- Don't let `project_gen.py` output claims without attached evidence.
- Don't reach for Document Intelligence (OCR) unless a paper's text extraction actually fails — most academic PDFs don't need it and it costs more.

## Testing / validation

When adding retrieval or Q&A logic, validate against a small fixed set of 3–5 sample papers with manually known answers (e.g., "Paper 2 and Paper 4 both mention latency as a limitation") so regressions in grounding are catchable before demo day.
