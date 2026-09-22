import { useState } from "react";
import { ApiError, askQuestionRetrieved } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { GroundedAnswer } from "../../types";
import { CitationList, CitationModalProvider, EvidencePanel } from "../shared/Citation";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PipelineWorkflowBanner from "../shared/PipelineWorkflowBanner";
import PageShell from "../PageShell";

export default function QAPage() {
  const { library } = useAppData();
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<{ question: string; answer: GroundedAnswer }[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleAsk() {
    if (!question.trim()) return;
    setStatus("loading");
    setError(null);
    const asked = question.trim();
    try {
      const answer = await askQuestionRetrieved(asked, 5);
      setHistory((prev) => [{ question: asked, answer }, ...prev]);
      setQuestion("");
      setStatus("idle");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Q&A request failed.");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Grounded Q&A"
      description="Ask questions across your uploaded and discovered research papers. Every answer is backed by verifiable citations and chunks."
    >
      <PipelineWorkflowBanner />

      <CitationModalProvider>
        <div className="bg-card border border-border p-5 mb-6">
          <div className="flex gap-3">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              placeholder={
                library.length > 0
                  ? `Ask across ${library.length} papers in your active context...`
                  : "What is the primary bottleneck in distributed training?"
              }
              className="flex-1 border border-border bg-background px-4 py-2.5 text-sm text-foreground focus:outline-none focus:border-[#FF6B2C]"
            />
            <button
              onClick={handleAsk}
              disabled={!question.trim() || status === "loading"}
              className="bg-[#FF6B2C] text-white font-bold uppercase px-6 py-2.5 text-xs tracking-wider cursor-pointer hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              {status === "loading" ? "Searching…" : "Ask Question"}
            </button>
          </div>
        </div>

        {status === "loading" && <div className="mt-6"><LoadingState label="Retrieving evidence and answering with citations…" /></div>}
        {status === "error" && error && (
          <div className="mt-6">
            <ErrorState message={error} onRetry={handleAsk} />
          </div>
        )}

        <div className="space-y-4">
          {history.map((entry, i) => (
            <div key={i} className="bg-card border border-border p-6 font-mono">
              <p className="text-xs font-bold uppercase text-[#FF6B2C] mb-2">{entry.question}</p>
              <p className="text-foreground text-sm leading-relaxed">{entry.answer.answer}</p>
              {!entry.answer.evidence_sufficient && (
                <p className="text-xs text-amber-500 font-bold mt-2">
                  Evidence insufficient — treat this answer with caution.
                </p>
              )}
              <div className="mt-4 pt-4 border-t border-border">
                <CitationList citations={entry.answer.citations} />
                <EvidencePanel citations={entry.answer.citations} />
              </div>
            </div>
          ))}
        </div>
      </CitationModalProvider>
    </PageShell>
  );
}
