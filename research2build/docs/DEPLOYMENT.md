# Research2Build — Retrieval Deployment & Operations Guide

This document describes how to deploy, configure, and operate the Research2Build evidence retrieval service in local development and production environments.

---

## Architecture Overview

```text
POST /retrieval/search
       │
       ▼
SemanticRetriever
       │
       ├── OpenAlexClient (Paper discovery)
       ├── chunk_text() (Sliding window text chunker)
       ├── EmbeddingProvider
       │     ├── HashEmbeddingProvider (Local dev fallback)
       │     └── AzureOpenAIEmbeddingProvider (Production: text-embedding-3-small)
       │
       └── BaseVectorStore
             ├── InMemoryVectorStore (Local dev fallback)
             └── AzureAISearchVectorStore (Production: HNSW Vector Search)
```

---

## 1. Quickstart (Local Development)

### Prerequisites

* Python 3.11+
* Pip

### Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Run FastAPI application
uvicorn backend.app.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`.

---

## 2. Environment Variables Configuration

Copy `.env.example` to `.env` and set the appropriate variables for your target environment:

```env
# OpenAlex Settings (Optional contact header)
OPENALEX_EMAIL=your-email@domain.com

# Azure OpenAI Credentials
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Azure AI Search Credentials
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-azure-search-key
AZURE_SEARCH_INDEX=research2build-evidence

# Production Hardening
# Set 'true' in local dev to enable in-memory & hashing fallback.
# Set 'false' in production so missing credentials or network errors fail fast.
RETRIEVAL_ALLOW_LOCAL_FALLBACK=false
```

---

## 3. Azure Provisioning Guide

### Azure OpenAI Setup
1. Create an Azure OpenAI resource in Azure Portal.
2. Deploy an embedding model (e.g. `text-embedding-3-small` or `text-embedding-ada-002`).
3. Set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`.

### Azure AI Search Setup
1. Create an Azure AI Search service (Basic or Standard SKU required for vector search).
2. Set `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, and `AZURE_SEARCH_INDEX`.
3. The application will automatically create or validate the HNSW vector index using `ensure_index_exists()`.

---

## 4. API Usage Examples

### Health Check

```bash
curl -X GET http://127.0.0.1:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "research2build-api"
}
```

### Search Evidence Chunks

```bash
curl -X POST http://127.0.0.1:8000/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning healthcare arrhythmia detection",
    "top_k": 3
  }'
```

**Response:**
```json
{
  "chunks": [
    {
      "chunk_id": "https://openalex.org/W123456789-chunk-0",
      "paper_id": "https://openalex.org/W123456789",
      "paper_title": "AI in Cardiology",
      "section": "Abstract",
      "page": null,
      "text": "Machine learning models detect cardiac arrhythmia accurately from ECG signals."
    }
  ]
}
```

---

## 5. Verification & Testing

Run full test suite:

```bash
python -m pytest
```
