import logging
import os

import requests
from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from backend.app.agents.analyzer import PaperAnalyzer
from backend.app.agents.deliverables import PRDDocument, generate_prd
from backend.app.agents.feasibility import FeasibilityAssessment, score_feasibility
from backend.app.agents.qa import GroundedQA
from backend.app.api_schemas import (
    CompareRequest,
    DiscoveredPaper,
    DiscoveryRequest,
    FeasibilityRequest,
    OpportunitiesRequest,
    PRDRequest,
    ProposalsRequest,
)
from backend.app.discovery.openalex_client import OpenAlexClient
from backend.app.research_intelligence.comparison import compare_papers
from backend.app.research_intelligence.limitations import find_recurring_limitations
from backend.app.research_intelligence.models import (
    PaperComparison,
    ProjectProposal,
    ResearchOpportunity,
)
from backend.app.research_intelligence.opportunities import generate_opportunities
from backend.app.research_intelligence.project_generator import generate_project_proposals
from backend.app.services.llm_service import LLMService
from shared.schemas import (
    AnalysisRequest,
    EvidenceChunk as SchemaEvidenceChunk,
    GroundedAnswer,
    HealthResponse,
    PaperAnalysis,
    QARequest,
    RetrievedQARequest,
    RetrievalRequest,
    RetrievalResult,
)

from app.retrieval.factory import get_retriever
from .ingestion import IngestionError, ingest_pdf
from .services.storage_service import InvalidUploadError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research2build.api")


app = FastAPI(
    title="Research2Build API",
    description="Evidence-grounded research analysis and discovery API",
    version="0.1.0",
)

# Phase 1: frontend and backend run as separate local dev servers on
# different ports (Vite default 5173, this repo's frontend on 5183), so
# the browser needs an explicit CORS allowance. FRONTEND_ORIGINS lets a
# deployed frontend origin be added via env var in later phases without
# code changes.
_default_dev_origins = [
    "http://localhost:5173",
    "http://localhost:5183",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5183",
]
_extra_origins = [o for o in os.environ.get("FRONTEND_ORIGINS", "").split(",") if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_dev_origins + _extra_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_llm_service() -> LLMService:
    raise RuntimeError(
        "LLM service is not configured for this environment"
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="research2build-api",
    )


@app.post("/papers/upload", response_model=list[SchemaEvidenceChunk])
async def upload_paper(file: UploadFile) -> list[SchemaEvidenceChunk]:
    content = await file.read()

    try:
        return ingest_pdf(
            filename=file.filename,
            content=content,
        )
    except (InvalidUploadError, IngestionError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.post("/retrieval/search", response_model=RetrievalResult)
async def search_evidence(
    request: RetrievalRequest,
) -> RetrievalResult:
    """
    Search OpenAlex & vector store for top-k grounded evidence chunks.
    """

    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string must not be empty.",
        )

    safe_query_log = request.query[:50] + (
        "..." if len(request.query) > 50 else ""
    )

    logger.info(
        "Executing retrieval query",
        extra={
            "query_sample": safe_query_log,
            "top_k": request.top_k,
        },
    )

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

        logger.info(
            "Retrieval completed",
            extra={"count": len(schema_chunks)},
        )

        return RetrievalResult(chunks=schema_chunks)

    except TimeoutError as err:
        logger.error(
            "Retrieval operation timed out",
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Retrieval service timeout.",
        ) from err

    except Exception as err:
        logger.error(
            "Retrieval failed",
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {str(err)}",
        ) from err


@app.post("/analysis", response_model=PaperAnalysis)
def analyze_paper(
    request: AnalysisRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> PaperAnalysis:
    try:
        analyzer = PaperAnalyzer(llm_service)

        return analyzer.analyze(
            paper_id=request.paper_id,
            paper_title=request.paper_title,
            evidence=request.evidence,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post("/qa", response_model=GroundedAnswer)
def answer_question(
    request: QARequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> GroundedAnswer:
    try:
        qa = GroundedQA(llm_service)

        return qa.answer(
            question=request.question,
            evidence=request.evidence,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post(
    "/qa/retrieve",
    response_model=GroundedAnswer,
)
async def answer_question_with_retrieval(
    request: RetrievedQARequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> GroundedAnswer:
    try:
        from backend.app.services.research_service import ResearchService

        service = ResearchService(llm_service)

        return await service.answer_question(
            question=request.question,
            top_k=request.top_k,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Retrieval service timeout.",
        ) from exc


@app.post("/discovery/search", response_model=list[DiscoveredPaper])
def discover_papers(request: DiscoveryRequest) -> list[DiscoveredPaper]:
    """Search OpenAlex for papers matching a topic query."""
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string must not be empty.",
        )

    try:
        papers = OpenAlexClient().search_papers(
            request.query,
            max_results=request.max_results,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAlex request failed: {exc}",
        ) from exc

    return [
        DiscoveredPaper(
            paper_id=paper.paper_id,
            title=paper.title,
            authors=paper.authors,
            year=paper.publication_year,
            abstract=paper.abstract or None,
            url=paper.url,
        )
        for paper in papers
    ]


@app.post("/research-intelligence/compare", response_model=PaperComparison)
def compare_analyses(request: CompareRequest) -> PaperComparison:
    """Compare structured analyses from two or more papers."""
    return compare_papers(request.analyses)


@app.post("/research-intelligence/opportunities", response_model=list[ResearchOpportunity])
def opportunities_from_analyses(request: OpportunitiesRequest) -> list[ResearchOpportunity]:
    """Surface potential research opportunities from recurring limitations."""
    limitations = find_recurring_limitations(request.analyses)
    return generate_opportunities(limitations)


@app.post("/research-intelligence/proposals", response_model=list[ProjectProposal])
def proposals_from_opportunities(request: ProposalsRequest) -> list[ProjectProposal]:
    """Generate buildable project proposals from research opportunities."""
    return generate_project_proposals(request.opportunities)


@app.post("/feasibility/score", response_model=FeasibilityAssessment)
def feasibility_score(request: FeasibilityRequest) -> FeasibilityAssessment:
    """Score a project proposal's feasibility and generate a roadmap."""
    return score_feasibility(request.proposal, request.constraints)


@app.post("/deliverables/prd", response_model=PRDDocument)
def deliverables_prd(request: PRDRequest) -> PRDDocument:
    """Synthesize a PRD for a project proposal."""
    return generate_prd(
        request.proposal,
        opportunity=request.opportunity,
        feasibility=request.feasibility,
    )