# Research2Build 🚀

> **Evidence-Grounded Research Analysis & Project Planning Platform**  
> An AI platform that analyzes research papers, identifies recurring limitations & opportunities, extracts evidence-grounded insights with exact citations, and generates feasibility-scored project proposals and PRDs.

---

## 📑 Table of Contents
- [Architecture & Monorepo Structure](#-architecture--monorepo-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Environment Setup](#1-environment-setup)
  - [2. Backend Setup & Run](#2-backend-setup--run)
  - [3. Frontend Setup & Run](#3-frontend-setup--run)
- [Service URLs & API Documentation](#-service-urls--api-documentation)
- [Environment Configuration Guide](#-environment-configuration-guide)
- [Running Tests](#-running-tests)
- [Azure Deployment Scripts](#-azure-deployment-scripts)

---

## 🏛 Architecture & Monorepo Structure

```
research2build/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application & API routes
│   │   ├── api_schemas.py              # Request/Response Pydantic schemas
│   │   ├── ingestion.py                # PDF extraction & text chunking
│   │   ├── agents/                     # LLM agents (Analyzer, QA, Feasibility, PRD)
│   │   ├── discovery/                  # OpenAlex & CORE paper discovery clients
│   │   ├── embeddings/                 # Azure OpenAI, Ollama & Local embeddings
│   │   ├── research_intelligence/      # Cross-paper synthesis & opportunities
│   │   ├── retrieval/                  # Azure AI Search & ChromaDB retrieval
│   │   └── services/                   # LLM factory & storage services
│   ├── requirements.txt                # Python backend dependencies
│   └── Dockerfile                      # Backend container configuration
├── frontend/
│   ├── src/                            # React + TypeScript source code
│   │   ├── components/                 # UI components
│   │   ├── pages/                      # Application views & dashboards
│   │   ├── services/                   # API client bindings
│   │   └── types/                      # Frontend TypeScript interfaces
│   ├── package.json                    # Node dependencies & scripts
│   └── vite.config.ts                  # Vite configuration
├── shared/                             # Shared contracts & schemas
├── scripts/                            # Azure deployment & test automation
└── main.py                             # Root FastAPI entrypoint
```

---

## 💻 Prerequisites

Ensure you have the following installed on your machine:

- **Python**: `3.10` or higher (`3.11` / `3.12` / `3.14` supported)
- **Node.js**: `18.0` or higher (includes `npm`)
- **Git**

---

## ⚡ Quick Start Guide

### 1. Environment Setup

Create a `.env` file:

#### Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

#### macOS / Linux:
```bash
cp .env.example .env
```

> **Note:** The backend is configured with `RETRIEVAL_ALLOW_LOCAL_FALLBACK=true` by default, meaning it can run locally without Azure credentials using ChromaDB and local/Ollama LLM fallbacks.

---

### 2. Backend Setup & Run

Open a terminal in this directory (`research2build/`):

#### **Windows (PowerShell):**

```powershell
# 1. Create virtual environment (if not already created)
python -m venv .venv

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Start the FastAPI server
python main.py
```

*Or run directly with `uvicorn` live reload:*
```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

#### **macOS / Linux:**

```bash
# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Start the FastAPI server
python main.py
# or: uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 3. Frontend Setup & Run

Open a **separate terminal** in `frontend/`:

#### **Windows / macOS / Linux:**

```bash
cd frontend

# 1. Install frontend packages
npm install

# 2. Start the Vite development server
npm run dev
```

---

## 🌐 Service URLs & API Documentation

Once running, access the services at:

| Service | URL | Description |
|---|---|---|
| **Frontend UI** | [http://localhost:5173](http://localhost:5173) | Main Web Interface |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI Core Service |
| **Interactive Docs (Swagger UI)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Test & explore API endpoints |
| **Alternative Docs (ReDoc)** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Clean API Reference |
| **Health Check Endpoint** | [http://localhost:8000/health](http://localhost:8000/health) | Service Health Status |

---

## ⚙️ Environment Configuration Guide

Edit `.env` to configure your LLM and vector store backends:

### Option A: Azure OpenAI + Azure AI Search (Production)
```ini
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-azure-api-key>
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_API_KEY=<your-azure-search-key>
AZURE_SEARCH_INDEX=research2build-evidence
RETRIEVAL_ALLOW_LOCAL_FALLBACK=false
```

### Option B: Local Development with Ollama
```ini
# Pull models first: `ollama pull qwen3:8b` & `ollama pull nomic-embed-text`
LLM_ENDPOINT=http://localhost:11434/v1/chat/completions
LLM_API_KEY=ollama
LLM_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
CHROMA_PATH=./chroma_db
RETRIEVAL_ALLOW_LOCAL_FALLBACK=true
```

### Option C: Standard OpenAI Key
```ini
LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
CHROMA_PATH=./chroma_db
RETRIEVAL_ALLOW_LOCAL_FALLBACK=true
```

---

## 🧪 Running Tests

To run the backend test suite:

```powershell
# From research2build directory with .venv activated
pytest
```

To run individual tests:
```powershell
pytest backend/app/test_api.py -v
pytest backend/app/test_upload_batch.py -v
```

---

## 🚀 Azure Deployment Scripts

Automated deployment scripts are located in `scripts/`:

```powershell
# Deploy infrastructure and app to Azure Container Apps & Static Web Apps
.\scripts\deploy-azure.ps1

# Test remote Azure endpoints
.\scripts\test-endpoints.ps1

# Teardown Azure resources
.\scripts\destroy-azure.ps1
```
