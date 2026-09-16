<style>
  h1, h2, h3 { border: none !important; }
  .r2b-badges img { margin: 2px; }
  .r2b-card {
    border: 1px solid #d0d7de;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 12px 0;
    background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(16,185,129,0.06));
  }
  .r2b-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
  }
  .r2b-done { background: #dafbe1; color: #116329; }
  .r2b-pending { background: #fff1e5; color: #9a5b13; }
  table.r2b-table th { background: #f6f8fa; }
</style>

<div align="center">

# 🔬 Research2Build

### Evidence-grounded research analysis and project planning platform

<p class="r2b-badges">
  <img alt="phase" src="https://img.shields.io/badge/phase-1%20%E2%80%94%20local%20skeleton-6366f1">
  <img alt="python" src="https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="fastapi" src="https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="frontend" src="https://img.shields.io/badge/frontend-React-61DAFB?logo=react&logoColor=white">
  <img alt="license" src="https://img.shields.io/badge/status-university%20project-lightgrey">
</p>

*papers → chunks → embeddings → retrieval → grounded LLM answers → opportunity → project proposal*

</div>

---

## ✨ What this is

Research2Build turns a set of uploaded research papers into:

- 📚 structured per-paper analysis (problem, method, results, limitations, future work)
- 💬 evidence-based Q&A, every answer traceable to a paper / section / page
- 💡 potential research opportunities inferred from recurring evidence across papers
- 🛠️ feasibility-checked project proposals with a basic roadmap

Built for an **AI-103 university project** on a limited Azure for Students budget ($100 credit).

<div class="r2b-card">

**The non-negotiable design constraint:** every generated claim must be traceable to a specific paper, section, and page. No code path may produce an ungrounded claim. See <a href="./claude.md">claude.md</a> for the full rationale.

</div>

## 🧭 Build phases

| Phase | Focus | Status |
|---|---|---|
| **1 — Local skeleton** | FastAPI backend, local PDF extraction/chunking, local vector store, direct LLM calls | 🟢 in progress |
| **2 — Azure swap-in** | Azure AI Search, Azure AI Foundry, Blob Storage — one service at a time | ⚪ not started |
| **3 — Deploy** | Azure Static Web Apps + Container Apps (scale-to-zero) | ⚪ not started |

## 🗂️ Repository structure

```text
research2build/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app + routes
│   │   ├── ingestion.py               # PDF -> text -> EvidenceChunk pipeline
│   │   └── services/
│   │       ├── storage_service.py     # upload validation + local storage
│   │       ├── text_service.py        # normalization + heading detection
│   │       └── chunking_service.py    # chunk assembly
│   └── requirements.txt
├── frontend/                          # React, added after backend MVP works
├── shared/
│   └── schemas.py                     # frozen contracts: EvidenceChunk, Citation
├── tests/
├── ARCHITECTURE.md
└── claude.md                          # build phase + scope discipline rules
```

## 🚀 Getting started

```bash
git clone <REPOSITORY_URL>
cd <REPOSITORY_NAME>/research2build

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/health`.

**Run the tests:**

```bash
pytest
```

## 📡 API surface (Phase 1)

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service liveness check |
| `POST` | `/papers/upload` | Upload a PDF → validated, stored locally, chunked into `EvidenceChunk[]` |

## 🔒 Frozen contracts

`EvidenceChunk` and `Citation` (`shared/schemas.py`) are the stable interface between **ingestion**, **retrieval/embeddings**, and **analysis/Q&A/RAG**. No existing field may be renamed, retyped, or removed without agreement across owners — see [`ARCHITECTURE.md`](./ARCHITECTURE.md).

<table class="r2b-table">
<tr><th>EvidenceChunk</th><th>Citation</th></tr>
<tr><td>

```python
chunk_id: str
paper_id: str
paper_title: str
section: str | None
page: int | None
text: str
```

</td><td>

```python
chunk_id: str
paper_id: str
paper_title: str
section: str | None
page: int | None
quote: str
```

</td></tr>
</table>

`EvidenceChunk` is what ingestion produces and retrieval indexes/returns. `Citation` is what every LLM-generated claim must carry as its grounding — build one with `Citation.from_chunk(chunk, quote=...)`.

## 👥 Team ownership

<div class="r2b-card">

| # | Owner | Module | Status |
|---|---|---|---|
| 1 | **Ingestion & Evidence** (M1) | `backend/app/ingestion.py`, `backend/app/services/` | <span class="r2b-pill r2b-done">✅ done</span> |
| 2 | Discovery & retrieval (M2) | `backend/app/retrieval.py`, `embeddings.py` | <span class="r2b-pill r2b-pending">⏳ pending</span> |
| 3 | Paper analysis & Q&A (M3) | `backend/app/agents/analyzer.py`, `qa.py` | <span class="r2b-pill r2b-pending">⏳ pending</span> |
| 4 | Opportunity, project, feasibility (M4) | `backend/app/agents/project_gen.py` | <span class="r2b-pill r2b-pending">⏳ pending</span> |
| 5 | Frontend & integration (M5) | `frontend/` | <span class="r2b-pill r2b-pending">⏳ pending</span> |

</div>

**M1 — Ingestion & Evidence, done:**

- ✅ PDF upload, validation, local storage (`storage_service.py`) — swap point for Azure Blob in Phase 2
- ✅ Text normalization, page numbering, heading/section detection (`text_service.py`)
- ✅ Chunking into standardized `EvidenceChunk`s (`chunking_service.py`)
- ✅ `EvidenceChunk` / `Citation` contract frozen at v1.0 for M2/M3 to build against
- ✅ 21 tests covering normalization, heading detection, chunking, upload validation, and end-to-end ingestion

## 🌱 Branching

Create one branch per member:

```bash
git checkout -b feature/member-1-ingestion
git checkout -b feature/member-2-discovery-retrieval
git checkout -b feature/member-3-analysis
git checkout -b feature/member-4-opportunity-feasibility
git checkout -b feature/member-5-frontend-integration
```

> Do not commit secrets, uploaded PDFs, generated datasets, or `.env` files.

## 🗣️ Responsible AI language

The system never claims to have *discovered* a research gap. Required phrasing everywhere, in generated text and UI copy alike:

- "Potential research opportunity" — never "research gap" or "discovery"
- "Inferred from recurring limitations in the provided papers" — never stated as fact
- Every generated opportunity/project carries a "Novelty confidence: requires human validation" note

---

<div align="center">

Built with ❤️ for AI-103 · see <a href="./claude.md">claude.md</a> for full engineering conventions

</div>
