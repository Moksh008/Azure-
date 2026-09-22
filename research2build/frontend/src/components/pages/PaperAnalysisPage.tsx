import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, analyzePaper, searchEvidence } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { EvidenceChunk, PaperAnalysis } from "../../types";
import AnalysisCard from "../shared/AnalysisCard";
import { CitationModalProvider } from "../shared/Citation";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PipelineWorkflowBanner from "../shared/PipelineWorkflowBanner";
import PageShell from "../PageShell";

export default function PaperAnalysisPage() {
  const { library, analyses, addAnalysis } = useAppData();
  const [paperId, setPaperId] = useState("");
  const [paperTitle, setPaperTitle] = useState("");
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    if (!paperId.trim() || !paperTitle.trim()) return;
    setStatus("loading");
    setError(null);
    try {
      // Prefer the evidence already attached to this paper in the library —
      // this is the paper's own chunks (upload) or abstract (discovery).
      // Only fall back to a backend-wide semantic search for a paper_id the
      // user typed manually that isn't in the library at all: searching by
      // title across the whole vector store risks pulling in unrelated
      // chunks from other papers once multiple papers have been indexed,
      // which breaks grounding for the paper actually being analyzed.
      const libraryPaper = library.find((p) => p.paper_id === paperId.trim());
      let evidence: EvidenceChunk[];
      if (libraryPaper && libraryPaper.evidence.length > 0) {
        evidence = libraryPaper.evidence;
      } else {
        const { chunks } = await searchEvidence(paperTitle.trim(), 10);
        const relevant = chunks.filter((c) => c.paper_id === paperId.trim());
        evidence = relevant.length > 0 ? relevant : chunks;
      }
      if (evidence.length === 0) {
        throw new Error("No evidence chunks found for this paper. Upload it or select from library first.");
      }
      const result = await analyzePaper(paperId.trim(), paperTitle.trim(), evidence);
      setAnalysis(result);
      addAnalysis(result);
      setStatus("done");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Analysis failed.",
      );
      setStatus("error");
    }
  }

  function handleSelectFromLibrary(p: { paper_id: string; title: string }) {
    setPaperId(p.paper_id);
    setPaperTitle(p.title);
  }

  return (
    <PageShell
      title="Paper Analysis"
      description="Structured, evidence-grounded extraction of problem, methodology, dataset, results, limitations, and future work — every field cites its source chunk."
    >
      <PipelineWorkflowBanner />

      {library.length > 0 && (
        <div className="bg-card border border-border p-4 mb-5">
          <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
            Select from Active Library ({library.length} available)
          </p>
          <div className="flex flex-wrap gap-2">
            {library.map((p) => {
              const isAnalyzed = analyses.some((a) => a.paper_id === p.paper_id);
              const isCurrent = paperId === p.paper_id;
              return (
                <button
                  key={p.paper_id}
                  onClick={() => handleSelectFromLibrary(p)}
                  className={`text-xs px-3 py-1.5 border transition-colors cursor-pointer flex items-center gap-1.5 ${
                    isCurrent
                      ? "bg-[#FF6B2C] text-white border-[#FF6B2C]"
                      : isAnalyzed
                      ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/40"
                      : "bg-background text-foreground border-border hover:border-[#FF6B2C]"
                  }`}
                >
                  <span className="font-bold">{p.paper_id}:</span> {p.title.slice(0, 40)}...
                  {isAnalyzed && <span className="text-[10px] font-bold uppercase">(Done)</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="bg-card border border-border p-5 grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-bold uppercase text-foreground">Paper ID</span>
          <input
            value={paperId}
            onChange={(e) => setPaperId(e.target.value)}
            placeholder="e.g. p1"
            className="border border-border bg-background px-3.5 py-2 text-sm text-foreground focus:outline-none focus:border-[#FF6B2C]"
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-bold uppercase text-foreground">Paper title</span>
          <input
            value={paperTitle}
            onChange={(e) => setPaperTitle(e.target.value)}
            placeholder="e.g. Federated Learning at Scale"
            className="border border-border bg-background px-3.5 py-2 text-sm text-foreground focus:outline-none focus:border-[#FF6B2C]"
          />
        </label>
        <button
          onClick={handleAnalyze}
          disabled={!paperId.trim() || !paperTitle.trim() || status === "loading"}
          className="sm:col-span-2 bg-[#FF6B2C] text-white font-bold uppercase py-2.5 text-xs tracking-wider cursor-pointer hover:opacity-90 disabled:opacity-40 transition-opacity"
        >
          {status === "loading" ? "Analyzing…" : "Analyze Paper"}
        </button>
      </div>

      {status === "loading" && <div className="mt-6"><LoadingState label="Retrieving evidence and analyzing…" /></div>}
      {status === "error" && error && (
        <div className="mt-6">
          <ErrorState message={error} onRetry={handleAnalyze} />
        </div>
      )}

      {/* Render Current Analysis */}
      {status === "done" && analysis && (
        <div className="mt-6">
          <CitationModalProvider>
            <AnalysisCard analysis={analysis} />
          </CitationModalProvider>
        </div>
      )}

      {/* Render Previously Generated Analyses */}
      {analyses.length > 0 && (
        <div className="mt-8 space-y-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            All Analyzed Papers in Session ({analyses.length})
          </h3>
          <CitationModalProvider>
            <div className="space-y-4">
              {analyses.map((a) => (
                <AnalysisCard key={a.paper_id} analysis={a} />
              ))}
            </div>
          </CitationModalProvider>

          <p className="text-xs text-muted-foreground mt-4 font-mono">
            {analyses.length >= 2 ? (
              <>
                {"Ready for next steps: "}
                <Link to="/compare" className="underline font-bold text-[#FF6B2C]">
                  Comparative Matrix &rarr;
                </Link>
                {" or "}
                <Link to="/opportunities" className="underline font-bold text-[#FF6B2C]">
                  Opportunity Finder &rarr;
                </Link>
              </>
            ) : (
              "Analyze at least one more paper to unlock Comparative Matrix."
            )}
          </p>
        </div>
      )}
    </PageShell>
  );
}
