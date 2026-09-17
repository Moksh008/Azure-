import { useState } from "react";
import { Link } from "react-router-dom";
import { comparePapers } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { PaperComparison } from "../../types";
import ComparisonTable from "../shared/ComparisonTable";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PageShell from "../PageShell";

export default function ComparisonPage() {
  const { analyses } = useAppData();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [comparison, setComparison] = useState<PaperComparison | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  function toggle(paperId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(paperId)) next.delete(paperId);
      else next.add(paperId);
      return next;
    });
  }

  async function handleCompare() {
    if (selected.size < 2) return;
    setStatus("loading");
    setError(null);
    try {
      const chosen = analyses.filter((a) => selected.has(a.paper_id));
      const result = await comparePapers(chosen);
      setComparison(result);
      setStatus("done");
    } catch {
      setError("Comparison failed.");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Cross-paper comparison"
      description="Compare shared themes, methods, datasets, and — most importantly — recurring limitations across multiple papers you've analyzed this session."
    >
      {analyses.length < 2 ? (
        <p className="text-muted">
          Analyze at least two papers on the{" "}
          <Link to="/analysis" className="underline font-semibold text-ink">
            Paper analysis
          </Link>{" "}
          page first.
        </p>
      ) : (
        <>
          <div className="bg-white rounded-2xl border border-border p-6">
            <p className="text-sm font-semibold text-ink mb-3">Select papers to compare</p>
            <div className="flex flex-wrap gap-2">
              {analyses.map((a) => (
                <button
                  key={a.paper_id}
                  onClick={() => toggle(a.paper_id)}
                  aria-pressed={selected.has(a.paper_id)}
                  className={`text-sm font-semibold rounded-full px-3.5 py-2 border cursor-pointer ${
                    selected.has(a.paper_id)
                      ? "bg-ink text-white border-ink"
                      : "bg-white text-ink border-border hover:bg-pill-bg"
                  }`}
                >
                  {a.paper_title}
                </button>
              ))}
            </div>
            <button
              onClick={handleCompare}
              disabled={selected.size < 2 || status === "loading"}
              className="mt-5 rounded-[10px] bg-ink text-white font-semibold px-6 py-3 cursor-pointer hover:opacity-90 disabled:opacity-40"
            >
              Compare selected
            </button>
          </div>

          {status === "loading" && <div className="mt-8"><LoadingState label="Comparing papers…" /></div>}
          {status === "error" && error && (
            <div className="mt-8">
              <ErrorState message={error} onRetry={handleCompare} />
            </div>
          )}
          {status === "done" && comparison && (
            <div className="mt-8">
              <ComparisonTable comparison={comparison} />
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
