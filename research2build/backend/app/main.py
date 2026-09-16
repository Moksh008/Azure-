import logging
from fastapi import FastAPI, HTTPException, UploadFile, status

from app.retrieval.factory import get_retriever
from shared.schemas import (
    EvidenceChunk as SchemaEvidenceChunk,
    HealthResponse,
    RetrievalRequest,
    RetrievalResult,
)

from .ingestion import IngestionError, ingest_pdf
from .services.storage_service import InvalidUploadError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research2build.api")

app = FastAPI(
    title="Research2Build API",
    description="Evidence-grounded research analysis and discovery API",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="research2build-api")


@app.post("/papers/upload", response_model=list[SchemaEvidenceChunk])
async def upload_paper(file: UploadFile) -> list[SchemaEvidenceChunk]:
    content = await file.read()
    try:
        return ingest_pdf(filename=file.filename, content=content)
    except (InvalidUploadError, IngestionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/retrieval/search", response_model=RetrievalResult)
async def search_evidence(request: RetrievalRequest) -> RetrievalResult:
    """
    Search OpenAlex & vector store for top-k grounded evidence chunks.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string must not be empty.",
        )

    safe_query_log = request.query[:50] + ("..." if len(request.query) > 50 else "")
    logger.info("Executing retrieval query", extra={"query_sample": safe_query_log, "top_k": request.top_k})

    try:
        retriever = get_retriever()
        chunks = await retriever.retrieve(
            question=request.query,
            top_k=request.top_k,
        )

        schema_chunks = []
        for chunk in chunks:
            schema_chunks.append(
                SchemaEvidenceChunk(
                    chunk_id=chunk.chunk_id,
                    paper_id=chunk.paper_id,
                    paper_title=chunk.title,
                    section=chunk.section,
                    page=chunk.page_number,
                    text=chunk.text,
                )
            )

        logger.info("Retrieval completed", extra={"count": len(schema_chunks)})
        return RetrievalResult(chunks=schema_chunks)

    except TimeoutError as err:
        logger.error("Retrieval operation timed out", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Retrieval service timeout.",
        ) from err
    except Exception as err:
        logger.error("Retrieval failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {str(err)}",
        ) from err
