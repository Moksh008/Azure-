# Research2Build

Evidence-grounded research analysis and project planning platform.

## Monorepo foundation

- `backend/` — FastAPI service and shared application contracts
- `frontend/` — React frontend placeholder
- `shared/` — Cross-member schemas and API contracts
- `docs/` — Architecture and contribution notes
- `tests/` — Shared test placeholder

## Getting started

```bash
git clone <REPOSITORY_URL>
cd <REPOSITORY_NAME>

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/health`.

## Branching

Create one branch per member:

```bash
git checkout -b feature/member-1-ingestion
git checkout -b feature/member-2-discovery-retrieval
git checkout -b feature/member-3-analysis
git checkout -b feature/member-4-opportunity-feasibility
git checkout -b feature/member-5-frontend-integration
```

Do not commit secrets, uploaded PDFs, generated datasets, or `.env` files.
