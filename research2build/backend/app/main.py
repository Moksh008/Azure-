import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from backend.app.agents.analyzer import PaperAnalyzer
from backend.app.agents.chat_router import LibrarySummaryEntry, classify_intent
from backend.app.agents.cross_paper_synthesizer import CrossPaperSynthesizer
from backend.app.agents.deliverables import PRDDocument, generate_prd
from backend.app.agents.feasibility import FeasibilityAssessment, score_feasibility
from backend.app.agents.qa import GroundedQA
from backend.app.api_schemas import (
    ChatRequest,
    ChatResponse,
    CompareRequest,
    DiscoveredPaper,
    DiscoveryRequest,
    FeasibilityRequest,
    FetchFullTextRequest,
    OpportunitiesRequest,
    PRDRequest,
    ProposalsRequest,
)
from backend.app.discovery.multi_source import search_all_sources, search_core_first
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
from backend.app.services.evidence_selection import select_evidence
from backend.app.services.llm_factory import get_llm_service
from backend.app.services.llm_service import (
    AzureFoundryLLMService,
    LLMService,
    start_chat_call_tracking,
)
from backend.app.services.pdf_fetch_service import PdfDownloadError, download_pdf
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
from app.retrieval.evidence import EvidenceChunk as RetrievalEvidenceChunk
from app.retrieval.factory import get_vector_store
from .ingestion import IngestionError, ingest_pdf
from .services.storage_service import MAX_FETCHED_PDF_BYTES, InvalidUploadError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research2build.api")

LLMServiceDep = LLMService | AzureFoundryLLMService

# Whole-paper analysis has no question to rank against, so rank chunks by the
# aspects the analysis extracts.
ANALYSIS_QUERY = (
    "problem objective goal motivation methodology method approach dataset "
    "data model architecture experiments results accuracy performance "
    "limitations future work"
)


app = FastAPI(
    title="Research2Build API",
    description="Evidence-grounded research analysis and discovery API",
    version="0.1.0",
)

# CORS configuration: Allow all origins so frontend on Static Web Apps or local dev can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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
        chunks = ingest_pdf(
            filename=file.filename,
            content=content,
        )

        retrieval_chunks = [
            RetrievalEvidenceChunk(
                chunk_id=chunk.chunk_id,
                paper_id=chunk.paper_id,
                title=chunk.paper_title,
                text=chunk.text,
                page_number=chunk.page,
                section=chunk.section,
            )
            for chunk in chunks
        ]
        vector_store = get_vector_store()
        if hasattr(vector_store, "ensure_index_exists"):
            vector_store.ensure_index_exists()
        vector_store.add_chunks(retrieval_chunks)
        logger.info(
            "Paper ingested and indexed",
            extra={"paper_id": chunks[0].paper_id, "chunk_count": len(chunks)},
        )
        return chunks
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
        indexed_chunks = get_vector_store().search(
            request.query,
            top_k=request.top_k,
        )
        if indexed_chunks:
            chunks = indexed_chunks
        else:
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
    llm_service: LLMServiceDep = Depends(get_llm_service),
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
    llm_service: LLMServiceDep = Depends(get_llm_service),
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
    llm_service: LLMServiceDep = Depends(get_llm_service),
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
    """Search OpenAlex (and CORE, when configured) for papers on a topic."""
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string must not be empty.",
        )

    try:
        papers = search_all_sources(
            request.query,
            max_results=request.max_results,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Paper search failed: {exc}",
        ) from exc

    return [
        DiscoveredPaper(
            paper_id=paper.paper_id,
            title=paper.title,
            authors=paper.authors,
            year=paper.publication_year,
            abstract=paper.abstract or None,
            url=paper.url,
            pdf_url=paper.pdf_url,
        )
        for paper in papers
    ]


@app.post("/papers/fetch-fulltext", response_model=list[SchemaEvidenceChunk])
def fetch_fulltext(request: FetchFullTextRequest) -> list[SchemaEvidenceChunk]:
    """Download a discovered paper's open-access PDF and run it through the
    same extraction pipeline as a manual upload, so it gets real full-text
    evidence (page/section-grounded) instead of just its OpenAlex abstract.

    Not every discovered paper has an OA PDF — callers only send this when
    DiscoveredPaper.pdf_url was non-null. If that link fails (publisher
    throttling, oversized file, not actually a PDF), the paper's other
    open-access locations known to OpenAlex are tried before giving up.

    Plain `def` on purpose: downloading is blocking, so FastAPI runs this in
    its threadpool instead of freezing the event loop for every other request.
    """
    failures: list[str] = []
    tried: set[str] = set()

    def attempt(url: str) -> list[SchemaEvidenceChunk] | None:
        tried.add(url)
        try:
            content = download_pdf(url)
            return ingest_pdf(
                filename="paper.pdf",
                content=content,
                paper_title=request.title,
                paper_id_override=request.paper_id,
                max_bytes=MAX_FETCHED_PDF_BYTES,
            )
        except (PdfDownloadError, InvalidUploadError, IngestionError) as exc:
            logger.warning("Full-text fetch failed for %s: %s", url, exc)
            failures.append(f"{url}: {exc}")
            return None

    chunks = attempt(request.pdf_url)
    if chunks is not None:
        return chunks

    # Alternate locations come from OpenAlex, so they only exist for its ids
    # (CORE-sourced papers have "core:<id>" ids and just the one link).
    alternates = (
        OpenAlexClient().pdf_candidates(request.paper_id)
        if "openalex.org" in request.paper_id
        else []
    )
    for alternate in alternates:
        if alternate in tried:
            continue
        chunks = attempt(alternate)
        if chunks is not None:
            return chunks

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            f"Could not get the full text ({len(tried)} open-access "
            f"location(s) tried). First error: {failures[0]}"
        ),
    )


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


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    llm_service: LLMServiceDep = Depends(get_llm_service),
) -> ChatResponse:
    """Unified chat workflow: classify intent, then reuse the same pipeline
    functions the dedicated /discovery, /analysis, and /qa routes call.

    Stateless like the rest of the API — the caller (frontend) supplies the
    paper library and selected evidence on every call.
    """
    start_chat_call_tracking()
    logger.info(
        "Chat request: message_chars=%d selected_chunks=%d selected_papers=%d",
        len(request.message),
        len(request.evidence),
        len({chunk.paper_id for chunk in request.evidence}),
    )
    library_summary = [
        LibrarySummaryEntry(paper_id=p.paper_id, title=p.title, source=p.source)
        for p in request.library
    ]
    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    try:
        parsed = classify_intent(
            llm_service,
            message=request.message,
            history=history_dicts,
            library=library_summary,
            has_selected_evidence=bool(request.evidence),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Chat routing failed: {exc}",
        ) from exc

    if parsed.intent == "search":
        query = (parsed.query or request.message).strip()
        if not query:
            return ChatResponse(reply="What topic should I search for?", action="chat")
        try:
            papers, source = search_core_first(query, max_results=10)
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Paper search failed: {exc}",
            ) from exc
        discovered = [
            DiscoveredPaper(
                paper_id=paper.paper_id,
                title=paper.title,
                authors=paper.authors,
                year=paper.publication_year,
                abstract=paper.abstract or None,
                url=paper.url,
                pdf_url=paper.pdf_url,
            )
            for paper in papers
        ]
        reply = (
            f"Found {len(discovered)} paper(s) for \"{query}\" via {source}. "
            "Tick the ones you want to work with."
            if discovered
            else f"No papers found for \"{query}\". Try a different phrasing."
        )
        return ChatResponse(reply=reply, action="search", discovered_papers=discovered)

    if parsed.intent == "analyze":
        if not request.evidence:
            return ChatResponse(
                reply="I don't have evidence for any paper yet — select or upload one first.",
                action="chat",
            )

        # A resolved paper_id means "just this one"; otherwise analyze
        # every paper currently represented in the supplied evidence (i.e.
        # every selected paper) rather than forcing a single-paper pick.
        evidence_by_paper: dict[str, list] = {}
        for chunk in request.evidence:
            evidence_by_paper.setdefault(chunk.paper_id, []).append(chunk)

        if parsed.paper_id:
            if parsed.paper_id not in evidence_by_paper:
                return ChatResponse(
                    reply="I don't have evidence for that paper yet — select or upload it first.",
                    action="chat",
                )
            target_ids = [parsed.paper_id]
        else:
            target_ids = list(evidence_by_paper.keys())

        analyzer = PaperAnalyzer(llm_service)
        selected_by_paper: dict[str, list] = {}
        try:
            for paper_id in target_ids:
                paper_evidence = evidence_by_paper[paper_id]
                selected_evidence = select_evidence(
                    paper_evidence, ANALYSIS_QUERY, lead_chunks=1
                )
                selected_chars = sum(
                    len(chunk.text) for chunk in selected_evidence
                )
                logger.info(
                    "Chat analysis evidence: paper_id=%s input_chunks=%d "
                    "selected_chunks=%d selected_chars=%d "
                    "approx_selected_tokens=%d",
                    paper_id,
                    len(paper_evidence),
                    len(selected_evidence),
                    selected_chars,
                    (selected_chars + 3) // 4,
                )
                selected_by_paper[paper_id] = selected_evidence

            if len(target_ids) > 1:
                synthesis_question = request.message
                analyses = [
                    CrossPaperSynthesizer(llm_service).synthesize_for_ui(
                        question=synthesis_question,
                        evidence_by_paper=selected_by_paper,
                    )
                ]
            else:
                paper_id = target_ids[0]
                paper_evidence = selected_by_paper[paper_id]
                analyses = [
                    analyzer.analyze(
                        paper_id=paper_id,
                        paper_title=evidence_by_paper[paper_id][0].paper_title,
                        evidence=paper_evidence,
                    )
                ]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if len(analyses) == 1:
            reply = f"Here's the structured analysis for \"{analyses[0].paper_title}\"."
        else:
            titles = ", ".join(f'"{a.paper_title}"' for a in analyses)
            reply = f"Here's the structured analysis for {len(analyses)} papers: {titles}."
        return ChatResponse(reply=reply, action="analyze", analyses=analyses)

    if parsed.intent == "ask":
        question = (parsed.question or request.message).strip()
        if not request.evidence:
            return ChatResponse(
                reply="Select or upload at least one paper first, then ask me again.",
                action="chat",
            )
        try:
            qa = GroundedQA(llm_service)
            answer = qa.answer(
                question=question,
                evidence=select_evidence(request.evidence, question),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ChatResponse(reply=answer.answer, action="ask", answer=answer)

    return ChatResponse(
        reply=parsed.reply or "Tell me what you'd like to do — search, upload, or ask a question.",
        action="chat",
    )