import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { comparePapers } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import ComparisonTable from "../shared/ComparisonTable";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import MethodologyMatrix from "../shared/MethodologyMatrix";
import PipelineWorkflowBanner from "../shared/PipelineWorkflowBanner";
import PageShell from "../PageShell";

export default function ComparisonPage() {
  const { analyses, comparison: globalComparison, setComparison: setGlobalComparison } = useAppData();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">(
    globalComparison ? "done" : "idle"
  );
  const [error, setError] = useState<string | null>(null);

  // Default select all analyzed papers
  useEffect(() => {
    if (analyses.length >= 2 && selected.size === 0) {
      setSelected(new Set(analyses.map((a) => a.paper_id)));
    }
  }, [analyses]);

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
      setGlobalComparison(result);
      setStatus("done");
    } catch {
      setError("Comparison failed.");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Comparative Matrix"
      description="Compare shared themes, methods, datasets, and recurring limitations across multiple papers you've analyzed."
    >
      <PipelineWorkflowBanner />

      {analyses.length < 2 ? (
        <div className="bg-card border border-border p-6 font-mono text-sm">
          <p className="text-muted-foreground mb-3">
            Analyze at least two papers first to unlock comparative analysis.
          </p>
          <Link
            to="/analysis"
            className="inline-flex items-center gap-1 text-xs font-bold uppercase bg-[#FF6B2C] text-white px-4 py-2 hover:opacity-90 transition-opacity"
          >
            Go to Paper Analysis &rarr;
          </Link>
        </div>
      ) : (
        <>
          <div className="bg-card border border-border p-5">
            <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
              Select Papers to Compare ({selected.size} selected)
            </p>
            <div className="flex flex-wrap gap-2">
              {analyses.map((a) => {
                const isSelected = selected.has(a.paper_id);
                return (
                  <button
                    key={a.paper_id}
                    onClick={() => toggle(a.paper_id)}
                    aria-pressed={isSelected}
                    className={`text-xs font-semibold px-3 py-1.5 border transition-all cursor-pointer ${
                      isSelected
                        ? "bg-[#FF6B2C] text-white border-[#FF6B2C]"
                        : "bg-background text-foreground border-border hover:border-[#FF6B2C]"
                    }`}
                  >
                    <span className="font-bold">{a.paper_id}:</span> {a.paper_title}
                  </button>
                );
              })}
            </div>
            <div className="mt-4 flex items-center gap-3">
              <button
                onClick={handleCompare}
                disabled={selected.size < 2 || status === "loading"}
                className="bg-[#FF6B2C] text-white font-bold uppercase px-6 py-2.5 text-xs tracking-wider cursor-pointer hover:opacity-90 disabled:opacity-40 transition-opacity"
              >
                {status === "loading" ? "Comparing…" : "Generate Comparative Matrix"}
              </button>
              {globalComparison && (
                <Link
                  to="/opportunities"
                  className="text-xs font-bold uppercase text-[#FF6B2C] hover:underline"
                >
                  Proceed to Opportunity Finder &rarr;
                </Link>
              )}
            </div>
          </div>

          {status === "loading" && (
            <div className="mt-6">
              <LoadingState label="Comparing papers across dimensions…" />
            </div>
          )}
          {status === "error" && error && (
            <div className="mt-6">
              <ErrorState message={error} onRetry={handleCompare} />
            </div>
          )}
          {globalComparison && (
            <div className="mt-6 space-y-4">
              <MethodologyMatrix analyses={analyses.filter((a) => selected.has(a.paper_id))} />
              <ComparisonTable comparison={globalComparison} />
              <div className="p-4 bg-card border border-border flex items-center justify-between font-mono">
                <span className="text-xs text-muted-foreground">
                  Matrix generated and synced across workspace.
                </span>
                <Link
                  to="/opportunities"
                  className="text-xs font-bold uppercase bg-[#FF6B2C] text-white px-4 py-2 hover:opacity-90"
                >
                  Next Step: Find Research Opportunities &rarr;
                </Link>
              </div>
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
