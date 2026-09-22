import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { scoreFeasibility } from "../../lib/api";
import { useAppData } from "../../lib/AppDataContext";
import type { FeasibilityAssessment, FeasibilityConstraints, ProjectProposal } from "../../types";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
import PipelineWorkflowBanner from "../shared/PipelineWorkflowBanner";
import Roadmap from "../shared/Roadmap";
import ScoreCard from "../shared/ScoreCard";
import PageShell from "../PageShell";

interface LocationState {
  proposal?: ProjectProposal;
}

const SAMPLE_PROPOSAL: ProjectProposal = {
  proposal_id: "sample_proposal",
  title: "Model Compression and Quantization Toolkit",
  summary: "A modular toolkit for post-training quantization and structured pruning.",
  source_opportunity_ids: [],
  objectives: ["Quantize weights", "Profile memory", "Deploy compressed model"],
  proposed_methods: ["BitsAndBytes / AWQ quantization"],
  expected_outcomes: ["Reproducible compression pipeline"],
  feasibility_notes: "",
  problem_statement: "Large models demand excessive VRAM.",
  technical_approach: ["Python", "PyTorch", "BitsAndBytes"],
  key_features: ["Quantization profiler"],
  paper_ids: [],
  evidence: [],
  novelty_confidence: "Requires human validation",
};

export default function FeasibilityDashboardPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { proposals, feasibility: globalFeasibility, setFeasibility: setGlobalFeasibility } = useAppData();
  
  const passedProposal = (location.state as LocationState | null)?.proposal;
  const initialProposal = passedProposal || (proposals.length > 0 ? proposals[0] : SAMPLE_PROPOSAL);

  const [selectedProposal, setSelectedProposal] = useState<ProjectProposal>(initialProposal);
  const [constraints, setConstraints] = useState<FeasibilityConstraints>({
    team_size: 2,
    weeks_available: 8,
    budget_usd: 0,
    skills: ["Python", "React", "PyTorch"],
  });
  const [skillsInput, setSkillsInput] = useState("Python, React, PyTorch");
  const [assessment, setAssessment] = useState<FeasibilityAssessment | null>(globalFeasibility);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">(
    globalFeasibility ? "done" : "idle"
  );
  const [error, setError] = useState<string | null>(null);

  async function handleScore() {
    setStatus("loading");
    setError(null);
    const skills = skillsInput.split(",").map((s) => s.trim()).filter(Boolean);
    try {
      const result = await scoreFeasibility(selectedProposal, { ...constraints, skills });
      setAssessment(result);
      setGlobalFeasibility(result);
      setStatus("done");
    } catch {
      setError("Feasibility scoring failed.");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Feasibility Scorer"
      description="Score project proposals against your team's real constraints (team size, timeline, budget, skills) and synthesize realistic delivery roadmaps."
    >
      <PipelineWorkflowBanner />

      {proposals.length > 1 && (
        <div className="bg-card border border-border p-4 mb-5">
          <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
            Select Active Proposal ({proposals.length} Available)
          </p>
          <div className="flex flex-wrap gap-2">
            {proposals.map((p) => (
              <button
                key={p.proposal_id}
                onClick={() => setSelectedProposal(p)}
                className={`text-xs px-3 py-1.5 border transition-colors cursor-pointer ${
                  selectedProposal.proposal_id === p.proposal_id
                    ? "bg-[#FF6B2C] text-white border-[#FF6B2C] font-bold"
                    : "bg-background text-foreground border-border hover:border-[#FF6B2C]"
                }`}
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="bg-card border border-border p-5">
        <div className="pb-3 mb-4 border-b border-border">
          <p className="font-bold text-base text-foreground font-mono">{selectedProposal.title}</p>
          <p className="text-muted-foreground text-xs mt-1">{selectedProposal.summary}</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-bold uppercase text-foreground">Team size</span>
            <input
              type="number"
              min={1}
              value={constraints.team_size}
              onChange={(e) => setConstraints((c) => ({ ...c, team_size: Number(e.target.value) }))}
              className="border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:border-[#FF6B2C]"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-bold uppercase text-foreground">Weeks available</span>
            <input
              type="number"
              min={1}
              value={constraints.weeks_available}
              onChange={(e) => setConstraints((c) => ({ ...c, weeks_available: Number(e.target.value) }))}
              className="border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:border-[#FF6B2C]"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-bold uppercase text-foreground">Budget (USD)</span>
            <input
              type="number"
              min={0}
              value={constraints.budget_usd}
              onChange={(e) => setConstraints((c) => ({ ...c, budget_usd: Number(e.target.value) }))}
              className="border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:border-[#FF6B2C]"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-bold uppercase text-foreground">Team skills (comma-separated)</span>
            <input
              value={skillsInput}
              onChange={(e) => setSkillsInput(e.target.value)}
              placeholder="Python, PyTorch, React"
              className="border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:border-[#FF6B2C]"
            />
          </label>
        </div>

        <button
          onClick={handleScore}
          disabled={status === "loading"}
          className="mt-5 bg-[#FF6B2C] text-white font-bold uppercase px-6 py-2.5 text-xs tracking-wider cursor-pointer hover:opacity-90 disabled:opacity-40 transition-opacity"
        >
          {status === "loading" ? "Scoring Feasibility…" : "Score Feasibility"}
        </button>
      </div>

      {status === "loading" && <div className="mt-6"><LoadingState label="Evaluating risk, skills & timeline feasibility…" /></div>}
      {status === "error" && error && (
        <div className="mt-6">
          <ErrorState message={error} onRetry={handleScore} />
        </div>
      )}
      {assessment && (
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <ScoreCard assessment={assessment} />
          <Roadmap roadmap={assessment.roadmap} />
          <button
            onClick={() => navigate("/deliverables", { state: { proposal: selectedProposal, feasibility: assessment } })}
            className="md:col-span-2 bg-[#FF6B2C] text-white font-bold uppercase px-6 py-3 text-xs tracking-wider cursor-pointer hover:opacity-90 justify-self-start font-mono transition-opacity"
          >
            Generate PRD & MVP Scaffold &rarr;
          </button>
        </div>
      )}
    </PageShell>
  );
}
