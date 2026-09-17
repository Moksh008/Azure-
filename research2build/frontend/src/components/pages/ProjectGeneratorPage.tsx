import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { generateProposals } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import ProjectCard from "../shared/ProjectCard";
import PageShell from "../PageShell";

export default function ProjectGeneratorPage() {
  const navigate = useNavigate();
  const { opportunities, proposals, setProposals } = useAppData();
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
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
      title="Project generator"
      description="Buildable project proposals grounded directly in the opportunities above and their underlying evidence."
    >
      {opportunities.length === 0 ? (
        <p className="text-muted">
          Explore{" "}
          <Link to="/opportunities" className="underline font-semibold text-ink">
            opportunities
          </Link>{" "}
          first — proposals are generated from them.
        </p>
      ) : (
        <>
          <button
            onClick={handleGenerate}
            disabled={status === "loading"}
            className="rounded-[10px] bg-ink text-white font-semibold px-6 py-3 cursor-pointer hover:opacity-90 disabled:opacity-40 mb-6"
          >
            {status === "loading" ? "Generating…" : "Generate proposals"}
          </button>

          {status === "loading" && <LoadingState label="Generating proposals…" />}
          {status === "error" && error && <ErrorState message={error} onRetry={handleGenerate} />}
          {status === "done" && (
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
