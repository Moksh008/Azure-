import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getOpportunities } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import OpportunityCard from "../shared/OpportunityCard";
import PipelineWorkflowBanner from "../shared/PipelineWorkflowBanner";
import PageShell from "../PageShell";

export default function OpportunityExplorerPage() {
  const navigate = useNavigate();
  const { analyses, opportunities, setOpportunities } = useAppData();
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">(
    opportunities.length > 0 ? "done" : "idle"
  );
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
      title="Opportunity Finder"
      description="Recurring limitations across analyzed papers become actionable research & engineering opportunities — flagged with evidence grounding."
    >
      <PipelineWorkflowBanner />

      {analyses.length === 0 ? (
        <div className="bg-card border border-border p-6 font-mono text-sm">
          <p className="text-muted-foreground mb-3">
            Analyze at least one paper on the Paper Analysis page first to extract limitations and opportunities.
          </p>
          <Link
            to="/analysis"
            className="inline-flex items-center gap-1 text-xs font-bold uppercase bg-[#FF6B2C] text-white px-4 py-2 hover:opacity-90"
          >
            Go to Paper Analysis &rarr;
          </Link>
        </div>
      ) : (
        <>
          <div className="bg-card border border-border p-5 flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs font-bold uppercase text-foreground">
                Synthesizing Across {analyses.length} Paper(s)
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {analyses.map((a) => a.paper_title).join(", ")}
              </p>
            </div>
            <button
              onClick={handleExplore}
              disabled={status === "loading"}
              className="bg-[#FF6B2C] text-white font-bold uppercase px-6 py-2.5 text-xs tracking-wider cursor-pointer hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              {status === "loading" ? "Analyzing Limitations…" : "Find Opportunities"}
            </button>
          </div>

          {status === "loading" && (
            <div className="mt-6">
              <LoadingState label="Analyzing recurring limitations across papers…" />
            </div>
          )}
          {status === "error" && error && (
            <div className="mt-6">
              <ErrorState message={error} onRetry={handleExplore} />
            </div>
          )}
          {status === "done" && opportunities.length > 0 && (
            <div className="mt-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Identified Research Opportunities ({opportunities.length})
                </h3>
                <button
                  onClick={() => navigate("/projects")}
                  className="text-xs font-bold uppercase text-[#FF6B2C] hover:underline cursor-pointer"
                >
                  Generate Project Proposals &rarr;
                </button>
              </div>
              {opportunities.map((opp) => (
                <OpportunityCard
                  key={opp.opportunity_id}
                  opportunity={opp}
                  onGenerateProject={() => navigate("/projects")}
                />
              ))}
            </div>
          )}
          {status === "done" && opportunities.length === 0 && (
            <div className="mt-6 bg-card border border-border p-6 font-mono text-sm">
              <p className="text-foreground font-bold mb-2">No recurring opportunities found.</p>
              <p className="text-muted-foreground">
                An opportunity is only surfaced when the same limitation appears in at least two
                analyzed papers.{" "}
                {analyses.length < 2
                  ? `Only ${analyses.length} paper${analyses.length === 1 ? " has" : "s have"} been analyzed so far — analyze at least one more to unlock cross-paper matching.`
                  : "The limitations across your analyzed papers didn't overlap enough to cluster — try analyzing additional related papers."}
              </p>
              <Link
                to="/analysis"
                className="inline-flex items-center gap-1 mt-3 text-xs font-bold uppercase bg-[#FF6B2C] text-white px-4 py-2 hover:opacity-90"
              >
                Analyze Another Paper &rarr;
              </Link>
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
