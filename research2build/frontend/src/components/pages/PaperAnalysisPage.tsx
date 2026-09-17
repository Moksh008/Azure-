import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, analyzePaper, searchEvidence } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { PaperAnalysis } from "../../types";
import AnalysisCard from "../shared/AnalysisCard";
import { CitationModalProvider } from "../shared/Citation";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PageShell from "../PageShell";

export default function PaperAnalysisPage() {
  const { analyses, addAnalysis } = useAppData();
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
      const { chunks } = await searchEvidence(paperTitle.trim(), 10);
      const relevant = chunks.filter((c) => c.paper_id === paperId.trim());
      const evidence = relevant.length > 0 ? relevant : chunks;
      if (evidence.length === 0) {
        throw new Error("No evidence chunks found for this paper. Upload it first.");
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

  return (
    <PageShell
      title="Paper analysis"
      description="Structured, evidence-grounded extraction of problem, methodology, dataset, results, limitations, and future work — every field cites its source chunk."
    >
      <div className="bg-white rounded-2xl border border-border p-6 grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-semibold text-ink">Paper ID</span>
          <input
            value={paperId}
            onChange={(e) => setPaperId(e.target.value)}
            placeholder="e.g. p1"
            className="rounded-[10px] border border-border px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-mint-deep"
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-semibold text-ink">Paper title</span>
          <input
            value={paperTitle}
            onChange={(e) => setPaperTitle(e.target.value)}
            placeholder="e.g. Federated Learning at Scale"
            className="rounded-[10px] border border-border px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-mint-deep"
          />
        </label>
        <button
          onClick={handleAnalyze}
          disabled={!paperId.trim() || !paperTitle.trim() || status === "loading"}
          className="sm:col-span-2 rounded-[10px] bg-ink text-white font-semibold py-3 cursor-pointer hover:opacity-90 disabled:opacity-40"
        >
          {status === "loading" ? "Analyzing…" : "Analyze paper"}
        </button>
      </div>

      {status === "loading" && <div className="mt-8"><LoadingState label="Retrieving evidence and analyzing…" /></div>}
      {status === "error" && error && (
        <div className="mt-8">
          <ErrorState message={error} onRetry={handleAnalyze} />
        </div>
      )}
      {status === "done" && analysis && (
        <div className="mt-8">
          <CitationModalProvider>
            <AnalysisCard analysis={analysis} />
          </CitationModalProvider>
        </div>
      )}

      {analyses.length > 0 && (
        <p className="text-sm text-muted mt-8">
          {analyses.length} paper(s) analyzed this session
          {analyses.length >= 2 ? (
            <>
              {" — ready to "}
              <Link to="/compare" className="underline font-semibold text-ink">
                compare
              </Link>
              {" or "}
              <Link to="/opportunities" className="underline font-semibold text-ink">
                explore opportunities
              </Link>
              .
            </>
          ) : (
            ". Analyze at least one more to unlock comparison and opportunities."
          )}
        </p>
      )}
    </PageShell>
  );
}
