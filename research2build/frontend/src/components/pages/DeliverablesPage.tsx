import { useEffect, useState, type ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { ApiError, downloadPRDMarkdown, downloadScaffold, generatePRD } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { FeasibilityAssessment, PRDDocument, ProjectProposal } from "../../types";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PipelineWorkflowBanner from "../shared/PipelineWorkflowBanner";
import PageShell from "../PageShell";

/** Mirrors backend/app/agents/deliverables.py's PRDDocument.to_markdown(). */
function prdToMarkdown(prd: PRDDocument): string {
  const lines: string[] = [
    `# ${prd.title}`,
    "",
    `*Novelty confidence: ${prd.novelty_confidence}*`,
    "",
    "## Problem",
    prd.problem_statement || "_Not specified._",
    "",
    "## Evidence",
  ];
  lines.push(...(prd.evidence.length > 0 ? prd.evidence.map((e) => `- ${e}`) : ["_No supporting evidence excerpts were attached._"]));
  lines.push(
    "",
    "## Potential Opportunity",
    prd.opportunity_summary,
    "",
    "## Solution",
    prd.solution_summary,
    "",
    "## Expected Contribution",
  );
  lines.push(...(prd.expected_contribution.length > 0 ? prd.expected_contribution.map((c) => `- ${c}`) : ["_None specified._"]));
  lines.push("", "## Feasibility", prd.feasibility_summary, "", "## Roadmap");
  lines.push(...(prd.roadmap_summary.length > 0 ? prd.roadmap_summary.map((s) => `- ${s}`) : ["_No roadmap attached._"]));
  lines.push(
    "",
    "---",
    "This document was generated automatically from recurring limitations " +
      "observed across the supplied papers. It does not claim to have " +
      "discovered a research gap; all opportunity and novelty statements " +
      `require human validation (${prd.novelty_confidence}).`,
  );
  return lines.join("\n") + "\n";
}

interface LocationState {
  proposal?: ProjectProposal;
  feasibility?: FeasibilityAssessment;
}

function Section({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <div className="py-4 border-b border-border/70 last:border-b-0">
      <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">{heading}</p>
      {children}
    </div>
  );
}

export default function DeliverablesPage() {
  const location = useLocation();
  const state = location.state as LocationState | null;
  const { proposals, feasibility: globalFeasibility, prd: globalPrd, setPrd: setGlobalPrd } = useAppData();

  const passedProposal = state?.proposal;
  const effectiveProposal = passedProposal || (proposals.length > 0 ? proposals[0] : undefined);
  const effectiveFeasibility = state?.feasibility || globalFeasibility || undefined;

  const [prd, setPrd] = useState<PRDDocument | null>(globalPrd);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">(
    globalPrd ? "done" : effectiveProposal ? "idle" : "idle"
  );
  const [error, setError] = useState<string | null>(null);
  const [scaffoldStatus, setScaffoldStatus] = useState<"idle" | "loading" | "error">("idle");
  const [scaffoldError, setScaffoldError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!effectiveProposal) return;
    setStatus("loading");
    setError(null);
    try {
      const result = await generatePRD(effectiveProposal, undefined, effectiveFeasibility);
      setPrd(result);
      setGlobalPrd(result);
      setStatus("done");
    } catch {
      setError("PRD generation failed.");
      setStatus("error");
    }
  }

  function handleDownloadMarkdown() {
    if (!prd) return;
    downloadPRDMarkdown(prd, prdToMarkdown(prd));
  }

  async function handleDownloadScaffold() {
    if (!effectiveProposal) return;
    setScaffoldStatus("loading");
    setScaffoldError(null);
    try {
      await downloadScaffold(effectiveProposal);
      setScaffoldStatus("idle");
    } catch (err) {
      setScaffoldError(err instanceof ApiError ? err.message : "Scaffold download failed.");
      setScaffoldStatus("error");
    }
  }

  useEffect(() => {
    if (passedProposal && !globalPrd) {
      handleGenerate();
    }
    // eslint-disable-next-line
  }, [passedProposal?.proposal_id]);

  return (
    <PageShell
      title="PRD & Delivery Roadmap"
      description="A Product Requirements Document synthesized from problem statements, evidence, opportunities, solutions, feasibility, and step-by-step roadmap."
    >
      <PipelineWorkflowBanner />

      {!effectiveProposal && !prd && (
        <div className="bg-card border border-border p-6 font-mono text-sm">
          <p className="text-muted-foreground mb-3">
            Generate project proposals and feasibility assessments first to synthesize PRD deliverables.
          </p>
          <Link
            to="/projects"
            className="inline-flex items-center gap-1 text-xs font-bold uppercase bg-[#FF6B2C] text-white px-4 py-2 hover:opacity-90"
          >
            Go to Project Proposals &rarr;
          </Link>
        </div>
      )}

      {effectiveProposal && !prd && status !== "loading" && (
        <div className="bg-card border border-border p-5 mb-6 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs font-bold uppercase text-foreground">
              Target Proposal: {effectiveProposal.title}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Ready to generate complete product requirements document with novelty verification.
            </p>
          </div>
          <button
            onClick={handleGenerate}
            className="bg-[#FF6B2C] text-white font-bold uppercase px-6 py-2.5 text-xs tracking-wider cursor-pointer hover:opacity-90 transition-opacity"
          >
            Synthesize PRD
          </button>
        </div>
      )}

      {status === "loading" && <LoadingState label="Synthesizing PRD document…" />}
      {status === "error" && error && <ErrorState message={error} onRetry={handleGenerate} />}

      {prd && (
        <div className="bg-card border border-border p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap pb-4 border-b border-border">
            <div>
              <span className="inline-block border border-[#FF6B2C]/40 bg-[#FF6B2C]/10 text-[#FF6B2C] text-xs font-bold px-3 py-1 font-mono uppercase mb-2">
                Novelty: {prd.novelty_confidence}
              </span>
              <p className="font-bold text-xl text-foreground font-mono">{prd.title}</p>
            </div>
            <button
              onClick={handleDownloadMarkdown}
              className="border border-border bg-background px-4 py-2 text-xs font-bold uppercase text-foreground cursor-pointer hover:border-[#FF6B2C] flex items-center gap-1.5 transition-colors"
            >
              Download PRD (.md)
            </button>
          </div>

          <Section heading="Problem Statement">
            <p className="text-foreground text-sm leading-relaxed">{prd.problem_statement}</p>
          </Section>
          <Section heading="Supporting Literature Evidence">
            <ul className="space-y-2">
              {prd.evidence.map((e, i) => (
                <li key={i} className="text-xs text-muted-foreground font-mono bg-background p-2.5 border border-border">
                  “{e}”
                </li>
              ))}
            </ul>
          </Section>
          <Section heading="Potential Opportunity">
            <p className="text-foreground text-sm leading-relaxed">{prd.opportunity_summary}</p>
          </Section>
          <Section heading="Technical Solution">
            <p className="text-foreground text-sm leading-relaxed">{prd.solution_summary}</p>
          </Section>
          <Section heading="Expected Contributions">
            <ul className="space-y-1.5">
              {prd.expected_contribution.map((c, i) => (
                <li key={i} className="text-xs text-foreground flex gap-2 font-mono">
                  <span className="text-emerald-500 font-bold shrink-0">✓</span>
                  {c}
                </li>
              ))}
            </ul>
          </Section>
          <Section heading="Feasibility Assessment">
            <p className="text-foreground text-sm leading-relaxed">{prd.feasibility_summary}</p>
          </Section>
          <Section heading="Engineering Roadmap">
            <ul className="space-y-2">
              {prd.roadmap_summary.map((step, i) => (
                <li key={i} className="text-xs text-foreground font-mono p-2 bg-background border border-border">
                  <span className="font-bold text-[#FF6B2C] mr-2">Phase {i + 1}:</span>
                  {step}
                </li>
              ))}
            </ul>
          </Section>

          {effectiveProposal && (
            <div className="mt-6 border border-border bg-background p-4 font-mono">
              <p className="text-xs text-muted-foreground mb-3">
                Download starter engineering scaffold matching proposed tech stack (Python, requirements, directory layout).
              </p>
              <button
                onClick={handleDownloadScaffold}
                disabled={scaffoldStatus === "loading"}
                className="bg-[#FF6B2C] text-white font-bold uppercase px-4 py-2.5 text-xs cursor-pointer hover:opacity-90 disabled:opacity-40 transition-opacity"
              >
                {scaffoldStatus === "loading" ? "Preparing scaffold…" : "Download Starter Scaffold (.zip)"}
              </button>
              {scaffoldStatus === "error" && scaffoldError && (
                <p className="text-xs text-red-500 mt-2">{scaffoldError}</p>
              )}
            </div>
          )}
        </div>
      )}
    </PageShell>
  );
}
