from fastapi import FastAPI, HTTPException, UploadFile
from shared.schemas import EvidenceChunk, HealthResponse

from .ingestion import IngestionError, ingest_pdf
from .services.storage_service import InvalidUploadError

app = FastAPI(title="Research2Build API", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="research2build-api")


@app.post("/papers/upload", response_model=list[EvidenceChunk])
async def upload_paper(file: UploadFile) -> list[EvidenceChunk]:
    content = await file.read()
    try:
        return ingest_pdf(filename=file.filename, content=content)
    except (InvalidUploadError, IngestionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
