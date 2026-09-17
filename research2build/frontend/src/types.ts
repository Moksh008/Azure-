// Frontend types mirroring backend Pydantic contracts.
// shared/schemas.py, backend/app/research_intelligence/models.py,
// backend/app/agents/feasibility.py, backend/app/agents/deliverables.py

export interface EvidenceChunk {
  chunk_id: string;
  paper_id: string;
  paper_title: string;
  section: string | null;
  page: number | null;
  text: string;
}

export interface Citation {
  chunk_id: string;
  paper_id: string;
  paper_title: string;
  section: string | null;
  page: number | null;
  quote: string;
}

export interface GroundedClaim {
  claim: string;
  citations: Citation[];
}

export interface PaperAnalysis {
  paper_id: string;
  paper_title: string;
  problem: GroundedClaim | null;
  objective: GroundedClaim | null;
  methodology: GroundedClaim | null;
  dataset: GroundedClaim | null;
  models: GroundedClaim | null;
  results: GroundedClaim[];
  limitations: GroundedClaim[];
  future_work: GroundedClaim[];
}

export interface GroundedAnswer {
  answer: string;
  citations: Citation[];
  evidence_sufficient: boolean;
}

export interface PaperComparison {
  comparison_id: string;
  paper_ids: string[];
  shared_themes: string[];
  methodological_overlaps: string[];
  methodological_differences: string[];
  shared_datasets: string[];
  dataset_differences: string[];
  key_findings: string[];
  common_limitations: string[];
  all_limitations: string[];
  agreements: string[];
  differences: string[];
  contradictions: string[];
}

export interface ResearchOpportunity {
  opportunity_id: string;
  title: string;
  description: string;
  source_limitation_ids: string[];
  novelty_confidence: string;
  keywords: string[];
  paper_ids: string[];
  evidence: string[];
}

export interface ProjectProposal {
  proposal_id: string;
  title: string;
  summary: string;
  source_opportunity_ids: string[];
  objectives: string[];
  proposed_methods: string[];
  expected_outcomes: string[];
  feasibility_notes: string;
  problem_statement: string;
  technical_approach: string[];
  key_features: string[];
  paper_ids: string[];
  evidence: string[];
  novelty_confidence: string;
}

export interface FeasibilityConstraints {
  team_size: number;
  weeks_available: number;
  budget_usd: number;
  skills: string[];
}

export interface Milestone {
  phase: string;
  description: string;
  deliverables: string[];
  duration_weeks: number;
  start_week: number;
  end_week: number;
}

export interface RoadmapPlan {
  total_weeks: number;
  milestones: Milestone[];
}

export type FeasibilityLevel = "high" | "medium" | "low" | "not_feasible";

export interface FeasibilityAssessment {
  proposal_id: string;
  score: number;
  level: FeasibilityLevel;
  estimated_effort_weeks: number;
  skill_coverage: number;
  risks: string[];
  constraint_notes: string[];
  roadmap: RoadmapPlan;
}

export interface PRDDocument {
  proposal_id: string;
  title: string;
  problem_statement: string;
  evidence: string[];
  opportunity_summary: string;
  solution_summary: string;
  expected_contribution: string[];
  feasibility_summary: string;
  roadmap_summary: string[];
  novelty_confidence: string;
}

export interface OpenAlexPaper {
  paper_id: string;
  title: string;
  authors: string[];
  year: number | null;
  abstract: string | null;
  url: string | null;
}
