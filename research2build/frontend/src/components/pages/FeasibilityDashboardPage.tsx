import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { scoreFeasibility } from "../../lib/api";
import type { FeasibilityAssessment, FeasibilityConstraints, ProjectProposal } from "../../types";
import ErrorState from "../shared/ErrorState";
import LoadingState from "../shared/LoadingState";
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
  const proposal = (location.state as LocationState | null)?.proposal ?? SAMPLE_PROPOSAL;

  const [constraints, setConstraints] = useState<FeasibilityConstraints>({
    team_size: 2,
    weeks_available: 8,
    budget_usd: 0,
    skills: [],
  });
  const [skillsInput, setSkillsInput] = useState("");
  const [assessment, setAssessment] = useState<FeasibilityAssessment | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleScore() {
    setStatus("loading");
    setError(null);
    const skills = skillsInput.split(",").map((s) => s.trim()).filter(Boolean);
    try {
      const result = await scoreFeasibility(proposal, { ...constraints, skills });
      setAssessment(result);
      setStatus("done");
    } catch {
      setError("Feasibility scoring failed.");
      setStatus("error");
    }
  }

  return (
    <PageShell
      title="Feasibility dashboard"
      description="Score a project proposal against your team's real constraints and get a tailored roadmap."
    >
      {!(location.state as LocationState | null)?.proposal && (
        <p className="text-sm text-muted mb-6">
          No proposal was selected — scoring the sample proposal below. Start from{" "}
          <button onClick={() => navigate("/projects")} className="underline font-semibold text-ink">
            Project generator
          </button>{" "}
          to score your own.
        </p>
      )}

      <div className="bg-white rounded-2xl border border-border p-6">
        <p className="font-display font-bold text-lg text-ink">{proposal.title}</p>
        <p className="text-muted text-sm mt-1">{proposal.summary}</p>

        <div className="grid gap-4 sm:grid-cols-2 mt-6">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-semibold text-ink">Team size</span>
            <input
              type="number"
              min={1}
              value={constraints.team_size}
              onChange={(e) => setConstraints((c) => ({ ...c, team_size: Number(e.target.value) }))}
              className="rounded-[10px] border border-border px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-mint-deep"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-semibold text-ink">Weeks available</span>
            <input
              type="number"
              min={1}
              value={constraints.weeks_available}
              onChange={(e) => setConstraints((c) => ({ ...c, weeks_available: Number(e.target.value) }))}
              className="rounded-[10px] border border-border px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-mint-deep"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-semibold text-ink">Budget (USD)</span>
            <input
              type="number"
              min={0}
              value={constraints.budget_usd}
              onChange={(e) => setConstraints((c) => ({ ...c, budget_usd: Number(e.target.value) }))}
              className="rounded-[10px] border border-border px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-mint-deep"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-semibold text-ink">Team skills (comma-separated)</span>
            <input
              value={skillsInput}
              onChange={(e) => setSkillsInput(e.target.value)}
              placeholder="Python, PyTorch, React"
              className="rounded-[10px] border border-border px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-mint-deep"
            />
          </label>
        </div>

        <button
          onClick={handleScore}
          disabled={status === "loading"}
          className="mt-6 rounded-[10px] bg-ink text-white font-semibold px-6 py-3 cursor-pointer hover:opacity-90 disabled:opacity-40"
        >
          {status === "loading" ? "Scoring…" : "Score feasibility"}
        </button>
      </div>

      {status === "loading" && <div className="mt-8"><LoadingState label="Scoring feasibility…" /></div>}
      {status === "error" && error && (
        <div className="mt-8">
          <ErrorState message={error} onRetry={handleScore} />
        </div>
      )}
      {status === "done" && assessment && (
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <ScoreCard assessment={assessment} />
          <Roadmap roadmap={assessment.roadmap} />
          <button
            onClick={() => navigate("/deliverables", { state: { proposal, feasibility: assessment } })}
            className="md:col-span-2 rounded-[10px] bg-ink text-white font-semibold px-6 py-3 cursor-pointer hover:opacity-90 justify-self-start"
          >
            Generate PRD & scaffold
          </button>
        </div>
      )}
    </PageShell>
  );
}
