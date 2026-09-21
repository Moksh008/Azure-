import { useState } from "react";
import { ApiError, askQuestionRetrieved } from "../../lib/api";
import type { GroundedAnswer } from "../../types";
import { CitationList, CitationModalProvider, EvidencePanel } from "../shared/Citation";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PageShell from "../PageShell";

export default function QAPage() {
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
      description="Ask a question across your uploaded papers. Every answer is either backed by citations or explicitly marked as insufficiently supported — never a silent guess."
    >
      <CitationModalProvider>
        <div className="flex gap-3">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder="What is the primary bottleneck in distributed training?"
            className="flex-1 rounded-[10px] border border-border px-4 py-3 bg-white focus:outline-none focus:ring-2 focus:ring-mint-deep"
          />
          <button
            onClick={handleAsk}
            disabled={!question.trim() || status === "loading"}
            className="rounded-[10px] bg-ink text-white font-semibold px-6 cursor-pointer hover:opacity-90 disabled:opacity-40"
          >
            Ask
          </button>
        </div>

        {status === "loading" && <div className="mt-6"><LoadingState label="Retrieving evidence and answering…" /></div>}
        {status === "error" && error && (
          <div className="mt-6">
            <ErrorState message={error} onRetry={handleAsk} />
          </div>
        )}

        <div className="mt-8 space-y-4">
          {history.map((entry, i) => (
            <div key={i} className="bg-white rounded-2xl border border-border p-6">
              <p className="text-sm font-semibold text-muted mb-2">{entry.question}</p>
              <p className="text-ink">{entry.answer.answer}</p>
              {!entry.answer.evidence_sufficient && (
                <p className="text-xs text-coral font-semibold mt-2">
                  Evidence insufficient — treat this answer with caution.
                </p>
              )}
              <CitationList citations={entry.answer.citations} />
              <EvidencePanel citations={entry.answer.citations} />
            </div>
          ))}
        </div>
      </CitationModalProvider>
    </PageShell>
  );
}
