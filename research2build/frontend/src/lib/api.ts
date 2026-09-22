// Typed API client for the FastAPI backend. Every route here is live —
// see backend/app/main.py. The research-intelligence/feasibility/PRD
// routes are stateless by design: the caller always passes the objects
// it already has (e.g. PaperAnalysis results from /analysis) rather than
// IDs the server would need a database to resolve.

import type {
  ChatMessage,
  ChatResponse,
  EvidenceChunk,
  FeasibilityAssessment,
  FeasibilityConstraints,
  GroundedAnswer,
  LibraryPaperRef,
  OpenAlexPaper,
  PRDDocument,
  PaperAnalysis,
  PaperComparison,
  ProjectProposal,
  ResearchOpportunity,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(detail || `Request to ${path} failed`, res.status);
  }
  return res.json() as Promise<T>;
}

// -- paper upload / ingestion ---------------------------------------------

export async function uploadPaper(file: File): Promise<EvidenceChunk[]> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/papers/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(detail || "Upload failed", res.status);
  }
  return res.json();
}

export async function uploadPapersBatch(files: File[]): Promise<EvidenceChunk[]> {
  if (files.length === 1) {
    return uploadPaper(files[0]);
  }
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  const res = await fetch(`${API_BASE}/papers/upload-batch`, { method: "POST", body: form });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(detail || "Batch upload failed", res.status);
  }
  return res.json();
}

export async function fetchFullText(
  paperId: string,
  title: string,
  pdfUrl: string,
): Promise<EvidenceChunk[]> {
  return postJSON("/papers/fetch-fulltext", { paper_id: paperId, title, pdf_url: pdfUrl });
}

// -- retrieval + analysis + Q&A --------------------------------------------

export function searchEvidence(query: string, topK = 5): Promise<{ chunks: EvidenceChunk[] }> {
  return postJSON("/retrieval/search", { query, top_k: topK });
}

export function analyzePaper(
  paperId: string,
  paperTitle: string,
  evidence: EvidenceChunk[],
): Promise<PaperAnalysis> {
  return postJSON("/analysis", { paper_id: paperId, paper_title: paperTitle, evidence });
}

export function askQuestion(question: string, evidence: EvidenceChunk[]): Promise<GroundedAnswer> {
  return postJSON("/qa", { question, evidence });
}

export function askQuestionRetrieved(question: string, topK = 5): Promise<GroundedAnswer> {
  return postJSON("/qa/retrieve", { question, top_k: topK });
}

// -- topic discovery (OpenAlex) --------------------------------------------

export function discoverTopics(query: string, maxResults = 20): Promise<OpenAlexPaper[]> {
  return postJSON("/discovery/search", { query, max_results: maxResults });
}

// -- research intelligence pipeline ----------------------------------------

export function comparePapers(analyses: PaperAnalysis[]): Promise<PaperComparison> {
  return postJSON("/research-intelligence/compare", { analyses });
}

export function getOpportunities(analyses: PaperAnalysis[]): Promise<ResearchOpportunity[]> {
  return postJSON("/research-intelligence/opportunities", { analyses });
}

export function generateProposals(opportunities: ResearchOpportunity[]): Promise<ProjectProposal[]> {
  return postJSON("/research-intelligence/proposals", { opportunities });
}

// -- feasibility + deliverables ---------------------------------------------

export function scoreFeasibility(
  proposal: ProjectProposal,
  constraints: FeasibilityConstraints,
): Promise<FeasibilityAssessment> {
  return postJSON("/feasibility/score", { proposal, constraints });
}

export function generatePRD(
  proposal: ProjectProposal,
  opportunity?: ResearchOpportunity,
  feasibility?: FeasibilityAssessment,
): Promise<PRDDocument> {
  return postJSON("/deliverables/prd", { proposal, opportunity, feasibility });
}

// -- unified chat workflow ---------------------------------------------------

export function sendChatMessage(
  message: string,
  history: ChatMessage[],
  library: LibraryPaperRef[],
  evidence: EvidenceChunk[],
): Promise<ChatResponse> {
  return postJSON("/chat", { message, history, library, evidence });
}

export { ApiError };
