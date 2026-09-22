import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { generateProposals } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PipelineWorkflowBanner from "../shared/PipelineWorkflowBanner";
import ProjectCard from "../shared/ProjectCard";
import PageShell from "../PageShell";

export default function ProjectGeneratorPage() {
  const navigate = useNavigate();
  const { opportunities, proposals, setProposals } = useAppData();
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">(
    proposals.length > 0 ? "done" : "idle"
  );
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (opportunities.length === 0) return;
    setStatus("loading");
    setError(null);
    try {
      const result = await generateProposals(opportunities);
      setProposals(result);
      setStatus("done");
    } catch {
      setError("Could not generate project proposals.");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Project Proposals"
      description="Buildable project proposals synthesized directly from discovered opportunities and underlying paper evidence."
    >
      <PipelineWorkflowBanner />

      {opportunities.length === 0 ? (
        <div className="bg-card border border-border p-6 font-mono text-sm">
          <p className="text-muted-foreground mb-3">
            Explore and extract opportunities first to generate grounded engineering project proposals.
          </p>
          <Link
            to="/opportunities"
            className="inline-flex items-center gap-1 text-xs font-bold uppercase bg-[#FF6B2C] text-white px-4 py-2 hover:opacity-90"
          >
            Go to Opportunity Finder &rarr;
          </Link>
        </div>
      ) : (
        <>
          <div className="bg-card border border-border p-5 flex items-center justify-between gap-4 flex-wrap mb-6">
            <div>
              <p className="text-xs font-bold uppercase text-foreground">
                Grounding on {opportunities.length} Opportunity Area(s)
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Ready to synthesize technical architectures and MVPs.
              </p>
            </div>
            <button
              onClick={handleGenerate}
              disabled={status === "loading"}
              className="bg-[#FF6B2C] text-white font-bold uppercase px-6 py-2.5 text-xs tracking-wider cursor-pointer hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              {status === "loading" ? "Synthesizing Proposals…" : "Generate Proposals"}
            </button>
          </div>

          {status === "loading" && <LoadingState label="Synthesizing buildable project architectures…" />}
          {status === "error" && error && <ErrorState message={error} onRetry={handleGenerate} />}
          {proposals.length > 0 && (
            <div className="grid gap-5 sm:grid-cols-2">
              {proposals.map((proposal) => (
                <ProjectCard
                  key={proposal.proposal_id}
                  proposal={proposal}
                  onCheckFeasibility={() => navigate("/feasibility", { state: { proposal } })}
                />
              ))}
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
