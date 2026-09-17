import { useEffect, useState, type ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { generatePRD } from "../../lib/api";
import type { FeasibilityAssessment, PRDDocument, ProjectProposal } from "../../types";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PageShell from "../PageShell";

interface LocationState {
  proposal?: ProjectProposal;
  feasibility?: FeasibilityAssessment;
}

function Section({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <div className="py-4 border-b border-row-border last:border-b-0">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">{heading}</p>
      {children}
    </div>
  );
}

export default function DeliverablesPage() {
  const location = useLocation();
  const state = location.state as LocationState | null;
  const proposal = state?.proposal;
  const feasibility = state?.feasibility;

  const [prd, setPrd] = useState<PRDDocument | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">(
    proposal ? "loading" : "idle",
  );
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!proposal) return;
    setStatus("loading");
    setError(null);
    try {
      const result = await generatePRD(proposal, undefined, feasibility);
      setPrd(result);
      setStatus("done");
    } catch {
      setError("PRD generation failed.");
      setStatus("error");
    }
  }

  useEffect(() => {
    handleGenerate();
    // eslint-disable-next-line
  }, [proposal?.proposal_id]);

  return (
    <PageShell
      title="Deliverables"
      description="A Product Requirements Document synthesized from the proposal's problem, evidence, opportunity, solution, feasibility, and roadmap — plus an honest MVP starter scaffold."
    >
      {!proposal && (
        <p className="text-muted">
          Score a proposal's feasibility on the{" "}
          <Link to="/feasibility" className="underline font-semibold text-ink">
            Feasibility dashboard
          </Link>{" "}
          first, then generate its PRD from there.
        </p>
      )}

      {status === "loading" && <LoadingState label="Synthesizing PRD…" />}
      {status === "error" && error && <ErrorState message={error} onRetry={handleGenerate} />}

      {status === "done" && prd && (
        <div className="bg-white rounded-2xl border border-border p-6">
          <span className="inline-block rounded-full bg-periwinkle/30 text-ink text-xs font-semibold px-3 py-1 mb-3">
            Novelty confidence: {prd.novelty_confidence}
          </span>
          <p className="font-display font-bold text-2xl text-ink">{prd.title}</p>

          <Section heading="Problem">
            <p className="text-ink">{prd.problem_statement}</p>
          </Section>
          <Section heading="Evidence">
            <ul className="space-y-1.5">
              {prd.evidence.map((e, i) => (
                <li key={i} className="text-sm text-ink/80">
                  “{e}”
                </li>
              ))}
            </ul>
          </Section>
          <Section heading="Potential opportunity">
            <p className="text-ink">{prd.opportunity_summary}</p>
          </Section>
          <Section heading="Solution">
            <p className="text-ink">{prd.solution_summary}</p>
          </Section>
          <Section heading="Expected contribution">
            <ul className="space-y-1.5">
              {prd.expected_contribution.map((c, i) => (
                <li key={i} className="text-sm text-ink flex gap-2">
                  <span className="text-mint-deep shrink-0" aria-hidden="true">✓</span>
                  {c}
                </li>
              ))}
            </ul>
          </Section>
          <Section heading="Feasibility">
            <p className="text-ink">{prd.feasibility_summary}</p>
          </Section>
          <Section heading="Roadmap">
            <ul className="space-y-1.5">
              {prd.roadmap_summary.map((step, i) => (
                <li key={i} className="text-sm text-ink">
                  {step}
                </li>
              ))}
            </ul>
          </Section>

          <div className="mt-6 rounded-[10px] bg-pill-bg text-sm text-muted p-4">
            MVP scaffold generation (README, backend/frontend stubs, requirements.txt) runs via{" "}
            <code className="text-ink">backend/app/agents/deliverables.py</code> and will be exposed as a
            downloadable zip once a scaffold-download API route is added.
          </div>
        </div>
      )}
    </PageShell>
  );
}
