import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getOpportunities } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import OpportunityCard from "../shared/OpportunityCard";
import PageShell from "../PageShell";

export default function OpportunityExplorerPage() {
  const navigate = useNavigate();
  const { analyses, opportunities, setOpportunities } = useAppData();
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleExplore() {
    if (analyses.length === 0) return;
    setStatus("loading");
    setError(null);
    try {
      const result = await getOpportunities(analyses);
      setOpportunities(result);
      setStatus("done");
    } catch {
      setError("Could not generate opportunities.");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Opportunity explorer"
      description="Recurring limitations across the papers you've analyzed become potential research opportunities — never claimed as a discovered gap, always flagged for human validation."
    >
      {analyses.length === 0 ? (
        <p className="text-muted">
          Analyze at least one paper on the{" "}
          <Link to="/analysis" className="underline font-semibold text-ink">
            Paper analysis
          </Link>{" "}
          page first.
        </p>
      ) : (
        <>
          <div className="bg-white rounded-2xl border border-border p-6 flex items-center justify-between gap-4 flex-wrap">
            <p className="text-sm text-muted">
              {analyses.length} paper(s) analyzed this session: {analyses.map((a) => a.paper_title).join(", ")}
            </p>
            <button
              onClick={handleExplore}
              disabled={status === "loading"}
              className="rounded-[10px] bg-ink text-white font-semibold px-6 py-3 cursor-pointer hover:opacity-90 disabled:opacity-40"
            >
              Explore opportunities
            </button>
          </div>

          {status === "loading" && <div className="mt-8"><LoadingState label="Analyzing recurring limitations…" /></div>}
          {status === "error" && error && (
            <div className="mt-8">
              <ErrorState message={error} onRetry={handleExplore} />
            </div>
          )}
          {status === "done" && (
            <div className="mt-8 space-y-4">
              {opportunities.length === 0 && (
                <p className="text-muted">No recurring limitations found across these papers yet.</p>
              )}
              {opportunities.map((opp) => (
                <OpportunityCard
                  key={opp.opportunity_id}
                  opportunity={opp}
                  onGenerateProject={() => navigate("/projects")}
                />
              ))}
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
